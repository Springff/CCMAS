"""
BioInfoMAS 生产级使用示例
展示完整的LLM工具调用能力和多智能体协作
"""

import logging
from system_production import BioInfoMASProduction

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_motif_identification():
    """
    示例: 完整的motif识别与分析工作流
    """
    system = BioInfoMASProduction(verbose=True)
    
    research_goal = """
    分析PDAC数据（细胞空间位置信息：D:\Desktop\Agent\BioInfoMAS\input\T2b5_spatial.csv，细胞基因表达信息：D:\Desktop\Agent\BioInfoMAS\input\sparse_matrix.txt，基因名：D:\Desktop\Agent\BioInfoMAS\input\gene_names.txt），识别其中经常出现的细胞模体，并分析其生物学意义。
    """
    
    result = system.run_analysis(
        research_goal=research_goal.strip()
    )
    
    print("\n[结果] 模体识别与分析完成。")
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # output_path = system.save_results(output_dir="BioInfoMAS/results/deg_analysis")
    # print(f"✓ 详细结果已保存到: {output_path}")
    # print(f"✓ 任务ID: {result.get('task_id')}")
    
    return result


def main():
    """
    运行所有生产级示例
    """
    print("\n" + "="*70)
    print("BioInfoMAS 生产级系统 - 完整工具调用演示")
    print("="*70)
    example_motif_identification()
 

if __name__ == "__main__":
    main()
