from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class AnalysisInput(BaseModel):
    documents: List[str] = []
    node_ids: List[str] = []
    concept_ids: List[str] = []
    options: Dict[str, Any] = {}

class AnalysisProvenance(BaseModel):
    source_documents: List[str]
    source_nodes: List[str]
    model: str
    model_version: str
    prompt_version: str
    created_at: datetime

class AnalysisResult(BaseModel):
    analysis_id: str
    analysis_type: str
    result_s3_key: str           # always JSON
    result_md_s3_key: Optional[str] = None
    provenance: AnalysisProvenance

class BaseAnalysisJob(ABC):
    @abstractmethod
    async def run(self, input: AnalysisInput, analysis_id: str) -> AnalysisResult:
        pass
