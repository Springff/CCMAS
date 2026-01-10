# BioInfoMAS 生产级部署指南

## 📋 项目概述

**BioInfoMAS** 是一个生产就绪的多智能体生物信息学分析平台，具有以下特点：

- ✅ **完整的工具调用能力** - 每个智能体都可以自动调用相应的工具
- ✅ **LLM驱动的推理** - 基于GPT-4或其他LLM的智能决策
- ✅ **生产级可靠性** - 完整的错误处理、日志记录和结果持久化
- ✅ **可扩展架构** - 易于添加新的分析工具和智能体
- ✅ **多样化分析** - 支持10+种生物信息学分析方法

## 🚀 快速部署

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv bioinfomas_env
source bioinfomas_env/bin/activate  # Linux/Mac
# 或
bioinfomas_env\Scripts\activate      # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. LLM配置

创建 `.env` 文件：

```bash
# OpenAI (推荐用于生产)
LLM_API_KEY=sk-your-key-here
LLM_MODEL_ID=gpt-4
LLM_BASE_URL=https://api.openai.com/v1

# 或 Azure OpenAI
# LLM_API_KEY=your-azure-key
# LLM_MODEL_ID=gpt-4
# LLM_BASE_URL=https://your-resource.openai.azure.com

# 系统配置
AUTOGEN_TIMEOUT=300
AUTOGEN_CACHE_SEED=42
VERBOSE=False
```

### 3. 验证安装

```bash
python -c "from system_production import BioInfoMASProduction; print('✓ BioInfoMAS 安装成功')"
```

## 📊 核心功能

### 5个专业化智能体，各自具有完整的工具调用能力

#### 1. **DataAgent** - 数据获取与预处理
```python
# 可调用的工具
- download_data()       # 从GEO、TCGA等下载
- quality_control()     # FastQC质量评估
- preprocess_data()     # 数据标准化、批次校正
```

#### 2. **AnalysisAgent** - 数据分析
```python
# 可调用的工具
- differential_expression_analysis()  # DESeq2/edgeR
- pathway_enrichment()                # KEGG/GO
- variant_calling()                   # 变异检测
- sequence_blast()                    # 序列搜索
```

#### 3. **KnowledgeAgent** - 知识推理
```python
# 可调用的工具
- query_knowledge_graph()              # 实体关系查询
- search_literature()                  # PubMed搜索
- interpret_results()                  # 结果解释
```

#### 4. **VisualizationAgent** - 可视化
```python
# 可调用的工具
- generate_volcano_plot()   # 火山图
- generate_heatmap()        # 热图
- generate_pca_plot()       # PCA图
- generate_report()         # 报告生成
```

#### 5. **OrchestratorAgent** - 任务协调
```python
# 功能
- plan_workflow()          # 工作流规划
- coordinate_agents()      # 智能体协调
```

## 💻 使用示例

### 基础使用

```python
from system_production import BioInfoMASProduction

# 1. 初始化系统
system = BioInfoMASProduction(verbose=True)

# 2. 定义分析目标
research_goal = """
分析乳腺癌患者的基因表达特征：
1. 从GEO下载数据
2. 进行质量控制
3. 差异表达分析
4. 通路富集
5. 生成报告
"""

# 3. 执行分析
result = system.run_analysis(
    research_goal=research_goal,
    parameters={
        "fdr_threshold": 0.05,
        "log2fc_threshold": 1.0,
        "database": "kegg"
    }
)

# 4. 保存结果
system.save_results(output_dir="./results")
```

### 运行完整示例

```bash
python production_examples.py
```

选择示例运行：
- 示例1: 差异表达分析
- 示例2: 全基因组变异检测
- 示例3: 单细胞RNA-seq分析
- 示例4: 生物通路分析
- 示例5: 批量分析

## 📈 生产部署最佳实践

### 1. 日志配置

```python
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bioinfomas.log'),
        logging.StreamHandler()
    ]
)
```

### 2. 错误处理

```python
try:
    result = system.run_analysis(research_goal)
    
    if result['status'] == 'error':
        logger.error(f"分析失败: {result['error']}")
        # 重试或回滚
    else:
        logger.info("分析成功")
        
except Exception as e:
    logger.exception("系统错误")
    # 错误恢复
```

### 3. 性能监控

```python
# 监控任务执行时间
import time

start = time.time()
result = system.run_analysis(research_goal)
elapsed = time.time() - start

logger.info(f"任务耗时: {elapsed:.2f}秒")
```

### 4. 结果管理

```python
# 按时间戳组织结果
import os
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"./results/{timestamp}"

system.save_results(output_dir=output_dir)
```

## 🔧 工具调用机制

### 智能体如何调用工具

1. **工具注册**
   ```python
   agent.register_tools(tools_definition, tool_map)
   ```

2. **LLM决策**
   - LLM分析任务需求
   - 自动选择合适的工具
   - 组装工具调用序列

3. **工具执行**
   ```python
   result = tool_function(parameters)
   ```

4. **结果反馈**
   - 工具结果返回给LLM
   - LLM进行下一步决策
   - 重复直至任务完成

## 📊 支持的分析类型

| 分析类型 | 描述 | 主要工具 |
|---------|------|---------|
| 差异表达 | 识别不同条件下的差异基因 | DESeq2, edgeR |
| 变异检测 | 识别SNP、Indel和结构变异 | GATK, SAMtools |
| 通路富集 | 功能注释和通路分析 | KEGG, GO, Reactome |
| 单细胞 | 细胞聚类和类型注释 | Seurat, Scanpy |
| 网络分析 | 蛋白质相互作用网络 | STRING, Cytoscape |
| 序列搜索 | 同源序列检索 | BLAST, FASTA |

## 🎯 生产部署检查清单

在部署到生产环境前，确保：

- [ ] ✅ LLM API密钥已配置
- [ ] ✅ 所有依赖已安装
- [ ] ✅ 日志系统已配置
- [ ] ✅ 错误处理已实现
- [ ] ✅ 结果存储路径已创建
- [ ] ✅ 备份策略已制定
- [ ] ✅ 监控告警已配置
- [ ] ✅ 用户权限已设置
- [ ] ✅ 数据隐私已确保
- [ ] ✅ 文档已完成

## 📝 API参考

### BioInfoMASProduction 类

```python
class BioInfoMASProduction:
    
    def __init__(llm_config=None, verbose=False):
        """初始化系统"""
    
    def run_analysis(research_goal: str, parameters: dict) -> dict:
        """执行分析工作流"""
    
    def save_results(output_dir: str = "./results") -> str:
        """保存分析结果"""
    
    def get_task_history() -> list:
        """获取任务历史"""
    
    def get_current_task() -> dict:
        """获取当前任务"""
```

## 🔐 安全建议

### 1. API密钥管理
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 限制API密钥权限

### 2. 数据隐私
- 敏感数据本地处理
- 加密数据传输
- 定期清理临时文件

### 3. 访问控制
- 限制系统访问权限
- 记录用户操作日志
- 定期审计访问记录

## 🚨 故障排查

### 问题1: "LLM_API_KEY not found"
```bash
# 检查环境变量
echo $LLM_API_KEY

# 重新加载环境配置
source .env
```

### 问题2: 任务超时
```python
# 增加超时时间
llm_config = {
    "timeout": 600  # 从300增加到600秒
}
system = BioInfoMASProduction(llm_config=llm_config)
```

### 问题3: 工具调用失败
```python
# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 检查工具注册
logger.info(f"已注册工具: {list(system.tools.keys())}")
```

## 📚 参考资源

- **AutoGen文档**: https://microsoft.github.io/autogen/
- **OpenAI API**: https://platform.openai.com/docs
- **BioPython**: https://biopython.org/
- **Plotly**: https://plotly.com/

## 📞 支持

遇到问题？

1. 查看日志文件
2. 检查配置文件
3. 查看代码示例
4. 阅读相关文档

## 🎉 总结

BioInfoMAS 是一个功能强大、可靠高效的生产级生物信息学分析平台。
通过完整的工具调用能力和LLM驱动的智能决策，
它能够自动完成复杂的生物信息学分析任务。

**现在就开始使用它吧！** 🚀

---

**版本**: 1.0.0 (生产就绪)  
**更新日期**: 2025年12月1日  
**支持**: Python 3.8+
