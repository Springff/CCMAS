"""
BioInfoMAS Configuration File
系统配置示例
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 系统基础配置
SYSTEM_CONFIG = {
    "system_name": "BioInfoMAS",
    "version": "1.0.0",
    "description": "Multi-Agent System for Bioinformatics Research",
}

# API配置
API_CONFIG = {
    "openai_api_key": os.getenv("LLM_API_KEY", ""),
    "openai_model": os.getenv("LLM_MODEL_ID", "gpt-4"),
    "api_base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
}

# 数据源配置
DATA_SOURCES = {
    "NCBI": {
        "base_url": "https://www.ncbi.nlm.nih.gov",
        "supports": ["fastq", "fasta", "vcf"]
    },
    "GEO": {
        "base_url": "https://www.ncbi.nlm.nih.gov/geo",
        "supports": ["expression_matrix", "metadata"]
    },
    "TCGA": {
        "base_url": "https://portal.gdc.cancer.gov",
        "supports": ["genomic", "clinical"]
    },
    "UniProt": {
        "base_url": "https://www.uniprot.org",
        "supports": ["protein_sequences", "annotations"]
    }
}

# 分析工具配置
ANALYSIS_TOOLS = {
    "differential_expression": ["deseq2", "edger", "limma"],
    "pathway_analysis": ["kegg", "go", "reactome"],
    "variant_calling": ["gatk", "samtools", "bcftools"],
    "sequence_alignment": ["bwa", "bowtie2", "hisat2"],
    "quality_control": ["fastqc", "multiqc"]
}

# 知识库配置
KNOWLEDGE_BASES = {
    "KEGG": "https://www.kegg.jp",
    "Reactome": "https://reactome.org",
    "GeneOntology": "http://geneontology.org",
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov"
}

# 可视化配置
VISUALIZATION_CONFIG = {
    "output_formats": ["html", "pdf", "svg", "png"],
    "interactive": True,
    "default_size": (800, 600),
    "color_palette": "viridis"
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "./logs/bioinfomas.log"
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_workers": 4,
    "cache_enabled": True,
    "cache_size": 1000,
    "timeout": 3600  # 秒
}
