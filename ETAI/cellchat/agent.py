import logging
import sys
import os
import json
bioinfomas_path = os.path.join(os.path.dirname(__file__), '..', '..')
bioinfomas_path = os.path.abspath(bioinfomas_path)

if bioinfomas_path not in sys.path:
    sys.path.insert(0, bioinfomas_path)
from system_production import BioInfoMASProduction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    system = BioInfoMASProduction(verbose=True)
    research_goal = """
    你是一个专业的生物信息学研究员。你的任务是对细胞图中出现在三角形模体('CAF', 'CAF', 'Malignant')中的细胞进行细胞通讯分析，细胞图保存在“D:/Desktop/ETAI/Result1/data/U7a25_graph.gml”，包含细胞类型和空间坐标的细胞信息文件在“D:/Desktop/ETAI/Result1/data/U7a25_spatial.csv”，基因表达信息保存文件在：“D:/Desktop/ETAI/Result1/data/sparse_matrix.txt”，基因名保存在：“D:/Desktop/ETAI/Result1/data/gene_names.txt”。
    """
    agent_name = "AnalysisAgent"
    result = system.agent_demonstration(agent_name, research_goal)
    result = json.loads(result)
       
    if isinstance(result, dict):
        final_output = result.get("final_output") 
        if final_output:
            print(final_output)
        else:
            print("\n任务完成")    


if __name__ == "__main__":
    main()
