"""
BioInfoMAS 生产级使用示例
展示完整的LLM工具调用能力和多智能体协作
"""

import sys
from datetime import datetime


class Tee:
    """同时写入终端和日志文件"""
    def __init__(self, file, stream):
        self.file = file
        self.stream = stream

    def write(self, data):
        try:
            self.stream.write(data)
        except UnicodeEncodeError:
            self.stream.write(data.encode(self.stream.encoding or 'utf-8', errors='replace').decode(self.stream.encoding or 'utf-8', errors='replace'))
        self.file.write(data)
        self.file.flush()

    def flush(self):
        self.stream.flush()
        self.file.flush()


# 在导入业务模块前设置日志重定向，确保捕获导入期间的所有输出
_log_file = None
_log_filename = None
if __name__ == "__main__":
    _log_filename = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    _log_file = open(_log_filename, "w", encoding="utf-8")
    sys.stdout = Tee(_log_file, sys.__stdout__)
    sys.stderr = Tee(_log_file, sys.__stderr__)

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
    
    research_goal = r"""
    分析PDAC数据（细胞空间位置信息：D:\virtual\CCMAS\input\U7a25_spatial.csv，细胞基因表达信息：D:\virtual\CCMAS\input\sparse_matrix.txt，基因名：D:\virtual\CCMAS\input\gene_names.txt），识别其中经常出现的细胞模体，并分析其生物学意义。
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
    try:
        print("\n" + "="*70)
        print("BioInfoMAS 生产级系统 - 完整工具调用演示")
        print("="*70)
        example_motif_identification()
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if _log_file:
            _log_file.close()
    print(f"日志已保存到: {_log_filename}")
 

if __name__ == "__main__":
    main()
