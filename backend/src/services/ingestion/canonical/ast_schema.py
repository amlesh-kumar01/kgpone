from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class NodeType(str, Enum):
    DOCUMENT = "DOCUMENT"
    CHAPTER = "CHAPTER"
    SECTION = "SECTION"
    SUBSECTION = "SUBSECTION"
    PARAGRAPH = "PARAGRAPH"
    LIST = "LIST"
    LIST_ITEM = "LIST_ITEM"
    TABLE = "TABLE"
    TABLE_ROW = "TABLE_ROW"
    TABLE_CELL = "TABLE_CELL"
    FIGURE = "FIGURE"
    CAPTION = "CAPTION"
    EQUATION = "EQUATION"
    DEFINITION = "DEFINITION"
    THEOREM = "THEOREM"
    PROOF = "PROOF"
    EXAMPLE = "EXAMPLE"
    ALGORITHM = "ALGORITHM"
    CODE_BLOCK = "CODE_BLOCK"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    OPTION = "OPTION"
    FORMULA = "FORMULA"
    CITATION = "CITATION"

class NodeSource(BaseModel):
    document_id: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    bbox: Optional[List[float]] = None   # [x0, y0, x1, y1]
    parser: str                          # "docling" | "llamaparse"
    parser_version: str
    confidence: float = 1.0

class ASTNode(BaseModel):
    id: str
    type: NodeType
    title: Optional[str] = None
    level: Optional[int] = None          # heading depth (1=chapter, 2=section…)
    parent_id: Optional[str] = None
    children: List["ASTNode"] = []
    text_content: str = ""
    source: NodeSource
    reading_order: Optional[int] = None
    
    # Type-specific fields
    latex: Optional[str] = None          # EQUATION/FORMULA
    variables: List[Dict[str, Any]] = [] # FORMULA
    headers: List[str] = []              # TABLE
    image_s3_key: Optional[str] = None   # FIGURE
    equation_label: Optional[str] = None
    question_type: Optional[str] = None
    marks: Optional[float] = None
    year: Optional[int] = None
    exam: Optional[str] = None

class ParserProvenance(BaseModel):
    parser_used: str
    parser_version: str
    quality_score: float
    fallback_reason: Optional[str] = None
    processing_timestamp: datetime

class CanonicalDocument(BaseModel):
    document_id: str
    title: str = ""
    authors: List[str] = []
    doc_type: str = ""
    toc: List[Dict[str, Any]] = []
    nodes: List[ASTNode] = []            # top-level nodes (chapters/sections)
    provenance: ParserProvenance
    metadata: Dict[str, Any] = {}
    processing_version: str = "2.0"
