import os
import torch
import pickle
import itertools
import re
import csv
import pandas as pd
import ast
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from tqdm import tqdm

os.environ["CUDA_VISIBLE_DEVICES"] = "0"


def candidate_trangle_motifs(nums, motif_path):
    numbers = list(range(nums))
    triangle = list(itertools.combinations_with_replacement(numbers, 3))
    save_pickle(triangle, motif_path)
    return {
        "status": "success",
        "num_motifs": len(triangle),
        "candidate_motifs_path": motif_path,
    }


def save_to_csv(data, filename, lists):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=lists)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def save_pickle(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def get_preprocessed_data(path, triangle):
    dataset = load_pickle(path)
    dataset_final = []
    prompt = "# CONTEXT #I want you to help me complete the subgraph matching task, that is, to determine whether a given subgraph exists on the large graph. Next, I will give you the information of the subgraph and the large graph respectively. <subgraph><index> {} </index><label> {} </label><edge> {} </edge></subgraph><large graph><index> {}</index><label> {} </label><edge> {}</edge></large graph>############## OBJECTIVE #You task is to determine whether a given subgraph exists on the large graph. Please note that both the large graph and the subgraph are undirected graphs, and the edges have no directionality, that is, (a, b) is equivalent to (b, a). ############## RESPONSE #"
    for j in range(len(triangle)):
        # 节点标签数据
        pat_node_id = [0, 1, 2]
        pat_edges = [(0, 1), (0, 2), (1, 2)]
        pat_node_labels = triangle[j]
        for i in range(len(dataset)):
            # 节点数量
            gra_num = dataset[i].vcount()
            gra_id_list = [int(x) for x in range(gra_num)]
            # 边的信息
            gra_edges = dataset[i].get_edgelist()
            # 节点标签数据
            gra_node_labels = dataset[i].vs["label"]
            id = i
            source = prompt.format(
                pat_node_id,
                pat_node_labels,
                pat_edges,
                gra_id_list,
                gra_node_labels,
                gra_edges,
            )
            question = (
                "Please think step by step. How many patterns exist on the graph?"
            )
            source_text = source + question
            dataset_final.append(
                {
                    "task": "2-5",
                    "id": id,
                    "input": source_text,
                    "pattern": pat_node_labels,
                    "prefix": "",
                }
            )
    return dataset_final


def evaluate_epoch(val_dataset, tokenizer, model):
    output = []
    model.eval()
    with torch.no_grad():
        for i in tqdm(range(len(val_dataset))):
            torch.cuda.empty_cache()
            messages = [
                {"role": "system", "content": val_dataset[i]["prefix"]},
                {"role": "user", "content": val_dataset[i]["input"]},
            ]
            input_ids = tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, return_tensors="pt"
            ).to(model.device)
            terminators = [
                tokenizer.eos_token_id,
                tokenizer.convert_tokens_to_ids("<|eot_id|>"),
            ]
            outputs = model.generate(
                input_ids=input_ids,
                max_new_tokens=2048,
                eos_token_id=terminators,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
            )
            response = outputs[0][input_ids.shape[-1] :]
            response_text = tokenizer.decode(response, skip_special_tokens=True)
            modified_text = re.search(r"There are (\d+)", response_text)
            if modified_text:
                output.append(
                    {
                        "pattern": val_dataset[i]["pattern"],
                        "id": val_dataset[i]["id"],
                        "predict": modified_text.group(1),
                    }
                )
            else:
                print("Extraction error:", response_text)
    return output


def calculate_motifs_numbers(motif_path, dataset_path, output_path):
    model_id = "./llama3"
    llm_dir = "./llama3-output-12000r-batchsize2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, load_in_8bit=True, device_map=0, torch_dtype=torch.float16
    )
    model = PeftModel.from_pretrained(model, llm_dir)
    triangle = load_pickle(motif_path)
    val_dataset = get_preprocessed_data(dataset_path, triangle)
    output = evaluate_epoch(val_dataset, tokenizer, model)
    list2 = ["pattern", "id", "predict"]
    save_to_csv(output, output_path, list2)
    return {
        "status": "各个模体在数据集中出现的次数已统计完成",
        "output_path": output_path,
    }


def identify_motif(motif_path1, motif_path2, true_label_path, single_label=True):
    if single_label:
        true_labels = pd.read_csv(
            true_label_path, header=None, names=["cell_name", "label"]
        )
        motifs = pd.read_csv(motif_path1)
        label_to_cell = dict(zip(true_labels["label"], true_labels["cell_name"]))
        true_labels["label"] = true_labels["label"].astype(int)
        label_to_cell = {int(k): v for k, v in label_to_cell.items()}
        # 取出现次数（predict）前10的 pattern
        top10_motifs = motifs.nlargest(10, "prediction")
        # 转换 pattern 字符串为实际元组，并替换为 cell_name
        result = []
        for _, row in top10_motifs.iterrows():
            pattern_str = row["pattern"]
            count = row["prediction"]
            pattern_tuple = ast.literal_eval(pattern_str)
            try:
                cell_tuple = tuple(label_to_cell[label] for label in pattern_tuple)
            except KeyError as e:
                print(
                    f"Warning: label {e} not found in true_labels. Skipping pattern {pattern_str}."
                )
                continue

            result.append(
                {"pattern": pattern_tuple, "cell_tuple": cell_tuple, "frequency": count}
            )

        motif_details = [
            {"cells": item["cell_tuple"], "frequency": item["frequency"]}
            for item in result
        ]

        return {"status": "success", "motifs": motif_details}
    else:
        pass
