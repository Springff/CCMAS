"""
BioInfoMAS - Multi-Agent System for Bioinformatics Research
生物信息学多智能体系统
"""

__version__ = "1.0.0"
__author__ = "BioInfoMAS Team"
__all__ = ["BioInfoMASProduction", "PlanAgent", "DataAgent", "MotifAgent", "AnalysisAgent", 
           "BioKnowledgeAgent"]

from system_production import BioInfoMASProduction
from agents.plan_agent import PlanAgent
from agents.data_agent import DataAgent
from agents.motif_agent import MotifAgent
from agents.analysis_agent import AnalysisAgent
from agents.bioknowledge_agent import BioKnowledgeAgent

