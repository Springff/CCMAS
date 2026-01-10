# BioInfoMAS - LLM驱动的生物信息学多智能体系统

## 📋 项目概述

**BioInfoMAS** 是一个基于 **AutoGen** 框架的先进多智能体系统，用于自动化复杂的生物信息学分析任务。系统通过5个专门化的LLM驱动智能体的协作，实现从数据获取、质量控制、分析、知识推理到可视化的完整工作流。

### 核心特性

- 🤖 **LLM驱动的智能体**：每个智能体都是基于大语言模型的ConversableAgent
- 🔧 **自动工具调用**：智能体可自动选择和调用14+个生物信息学工具
- 🧠 **自然语言交互**：用自然语言描述研究目标，系统自动规划执行
- 🔄 **多智能体协作**：通过AutoGen的group chat实现多智能体协调
- 📊 **端到端分析**：从原始数据到专业报告的完整自动化流程
- 🎯 **灵活易扩展**：易于添加新的分析工具和智能体

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户自然语言输入                            │
│          "分析乳腺癌的基因表达变化..."                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                OrchestratorAgent (协调者)                    │
│  - 理解研究目标                                             │
│  - 分解任务为子任务                                         │
│  - 协调其他智能体执行                                       │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────────┐
│ DataAgent   │ │AnalysisAgent │ │ KnowledgeAgent   │
│ - 下载数据   │ │ - 差异表达    │ │ - 知识图谱       │
│ - 质量控制   │ │ - 变异检测    │ │ - 文献搜索       │
│ - 预处理     │ │ - 通路富集    │ │ - 结果解释       │
└─────────────┘ └──────────────┘ └──────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │VisualizationAgent   │
            │ - 生成图表          │
            │ - 创建报告          │
            │ - 数据可视化        │
            └─────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  最终分析报告 + 图表  │
            └─────────────────────┘
```

## 🎯 5个核心智能体

### 1. **OrchestratorAgent** (协调者)
- 理解用户的自然语言研究目标
- 将复杂任务分解为具体的工作步骤
- 管理其他4个智能体的工作流程
- 整合最终的分析结果

### 2. **DataAgent** (数据智能体)
- 从GEO、TCGA、NCBI等数据库下载数据
- 执行FastQC质量控制
- 数据预处理（修剪适配器、去批次效应等）
- 格式转换（FASTQ→BAM→VCF）

### 3. **AnalysisAgent** (分析智能体)
- 差异表达分析（DESeq2、edgeR）
- 变异检测（SNP、indel、结构变异）
- 通路富集分析（GO、KEGG、Reactome）
- BLAST序列相似性搜索
- 统计学分析和假设检验

### 4. **KnowledgeAgent** (知识智能体)
- 查询生物知识图谱（KEGG、GO、Reactome）
- 在PubMed中搜索相关文献
- 解释分析结果的生物学意义
- 连接基础研究与临床应用

### 5. **VisualizationAgent** (可视化智能体)
- 生成专业数据可视化（火山图、热图、PCA等）
- 创建交互式HTML图表
- 撰写科研分析报告
- 为非专业人士总结关键发现

## 🛠️ 可调用的工具集

### 数据工具 (3个)
- `download_data()` - 从公共数据库下载
- `quality_control()` - FastQC质量控制
- `preprocess_data()` - 数据预处理

### 分析工具 (5个)
- `differential_expression_analysis()` - 差异表达
- `pathway_enrichment()` - 通路富集
- `variant_calling()` - 变异检测
- `sequence_blast()` - 序列搜索

### 知识工具 (3个)
- `query_knowledge_graph()` - 知识图谱查询
- `search_literature()` - 文献搜索
- `explain_biological_significance()` - 结果解释

### 可视化工具 (4个)
- `generate_volcano_plot()` - 火山图
- `generate_heatmap()` - 热图
- `generate_pca_plot()` - PCA图
- `generate_report()` - 报告生成

## 🚀 快速开始

### 1. 安装

```bash
# 克隆或下载项目
cd BioInfoMAS

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 填入你的 LLM API 密钥
# 示例 (OpenAI):
# LLM_API_KEY=sk-xxx...
# LLM_MODEL_ID=gpt-4
# LLM_BASE_URL=https://api.openai.com/v1
```

### 3. 基本使用

```python
from system import BioInfoMAS

# 创建系统
system = BioInfoMAS()

# 执行分析
result = system.execute_workflow(
    user_goal="分析乳腺癌的基因表达变化",
    verbose=True
)

# 保存结果
system.save_results()
```

### 4. 运行示例

```bash
# 运行预设示例
python example.py
```

## 📊 使用示例

### 示例 1: 差异表达分析

```python
goal = """
分析乳腺癌患者与健康对照组的基因表达差异：
1. 从GEO数据库下载数据集
2. 进行质量控制和预处理
3. 执行差异表达分析
4. 进行KEGG通路富集
5. 生成火山图和热图
6. 生成分析报告
"""

result = system.execute_workflow(goal)
```

### 示例 2: 全基因组变异检测

```python
goal = """
进行全基因组关联研究(GWAS)分析：
1. 下载GWAS数据集
2. 数据质量控制和样本过滤
3. 检测显著关联位点
4. 进行LD分析
5. 查询文献找相关基因
6. 生成曼哈顿图和QQ图
"""

result = system.execute_workflow(goal)
```

### 示例 3: 单细胞分析

```python
goal = """
分析单细胞RNA-seq数据：
1. 下载单细胞数据
2. 细胞过滤和标准化
3. 高度变异基因选择
4. 细胞聚类
5. 细胞类型注释
6. 细胞通讯分析
"""

result = system.execute_workflow(goal)
```

## 📁 项目结构

```
BioInfoMAS/
├── agents/                      # 智能体实现
│   ├── __init__.py
│   ├── orchestrator_agent.py    # 协调者智能体
│   ├── data_agent.py            # 数据智能体
│   ├── analysis_agent.py        # 分析智能体
│   ├── knowledge_agent.py       # 知识智能体
│   └── visualization_agent.py   # 可视化智能体
├── autogen_framework.py         # 工具定义和AutoGen配置
├── system.py                    # 系统主类
├── example.py                   # 使用示例
├── requirements.txt             # Python依赖
├── .env.example                 # 配置模板
├── README.md                    # 本文件
└── data/                        # 数据存储目录
    └── results/                 # 分析结果输出
```

## 🔧 LLM 提供商配置

### OpenAI (推荐)
```
LLM_API_KEY=sk-xxx...
LLM_MODEL_ID=gpt-4
LLM_BASE_URL=https://api.openai.com/v1
```

### Azure OpenAI
```
LLM_API_KEY=your-azure-key
LLM_MODEL_ID=gpt-4
LLM_BASE_URL=https://your-resource.openai.azure.com
```

### 本地 Ollama (免费)
```
LLM_API_KEY=not-needed
LLM_MODEL_ID=llama2
LLM_BASE_URL=http://localhost:11434
```

## 🎓 工作流示例

### 完整的生物信息学分析工作流

```
1. 【用户输入】
   ↓
2. 【OrchestratorAgent 分析需求】
   - 识别任务类型
   - 规划工作流
   ↓
3. 【DataAgent 处理数据】
   - 下载原始数据
   - 质量控制
   - 数据预处理
   ↓
4. 【AnalysisAgent 执行分析】
   - 差异表达分析
   - 通路富集分析
   ↓
5. 【KnowledgeAgent 推理解释】
   - 查询知识图谱
   - 搜索相关文献
   - 生物学意义解释
   ↓
6. 【VisualizationAgent 生成报告】
   - 创建图表
   - 撰写报告
   ↓
7. 【输出最终结果】
   - 专业分析报告
   - 数据可视化
   - 发现和结论
```

## ⚙️ 高级功能

### 批量处理

```python
system = BioInfoMAS()

tasks = [
    "分析数据集1的基因表达",
    "进行变异检测分析",
    "执行通路富集"
]

for task in tasks:
    result = system.execute_workflow(task)

# 查看任务历史
history = system.get_task_history()
```

### 自定义配置

```python
custom_config = {
    "config_list": [{
        "model": "gpt-4",
        "api_key": "sk-xxx",
        "base_url": "https://api.openai.com/v1"
    }],
    "timeout": 600,
    "cache_seed": 42
}

system = BioInfoMAS(llm_config=custom_config)
```

## 💡 最佳实践

1. **清晰的研究目标**：用具体的自然语言描述你的分析需求
2. **数据质量**：确保输入数据的质量，系统会自动进行质量控制
3. **参数设置**：根据数据特性设置合理的分析参数
4. **结果验证**：仔细审查分析结果和解释
5. **成本控制**：考虑使用 GPT-3.5-turbo 或本地模型降低成本

## 📝 文档

- **QUICK_START.md** - 快速开始指南
- **README.md** - 本文档
- **autogen_framework.py** - 工具定义详情
- **agents/*.py** - 每个智能体的系统提示

## 🤝 贡献

欢迎为本项目做出贡献！请：

1. Fork 项目
2. 创建特性分支
3. 提交Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

- [AutoGen](https://github.com/microsoft/autogen) - 多智能体框架
- [OpenAI](https://openai.com/) - LLM API
- 所有生物信息学工具和数据库

## 📞 支持

如有问题，请提出 Issue 或联系项目维护者。

---

**BioInfoMAS** - 让生物信息学研究变得更智能、更高效! 🧬🤖
