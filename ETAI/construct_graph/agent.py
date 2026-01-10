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
    你是一个专业的生物信息学研究员。你的任务是利用我给你提供的数据构建细胞图，原始数据在“D:\Desktop\Agent\BioInfoMAS\input\T2b5_spatial.csv”。
    """
    result = system.construct_graph(research_goal)
    result = json.loads(result)
       
    if isinstance(result, dict):
        final_output = result.get("final_output") 
        print(final_output)
    else:
        print("\n构建细胞图完成")    


if __name__ == "__main__":
    main()
