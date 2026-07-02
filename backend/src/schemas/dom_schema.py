from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DOMMetadata(BaseModel):
    """Metadata attached to a DOM Node or Chunk."""
    context_path: List[str] = Field(
        default_factory=list, 
        description="Hierarchical path of headings, e.g., ['Chapter 3', '3.1 Models']"
    )
    section_number: Optional[str] = Field(
        default=None,
        description="Numeric section prefix, e.g. '3.3' for '3.3 Feed-Forward Networks'"
    )
    headers: Optional[List[str]] = Field(
        default=None, 
        description="Column headers for table row chunks"
    )
    parent_table_title: Optional[str] = Field(
        default=None, 
        description="Title of the parent table, if applicable"
    )
    image_s3_key: Optional[str] = Field(
        default=None,
        description="S3 key of the extracted image for figure nodes"
    )
    document_id: Optional[str] = None
    course_offering_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

class DOMNode(BaseModel):
    """A node in the Document Object Model tree."""
    node_id: str
    parent_id: Optional[str] = None
    node_type: str = Field(
        description="e.g., 'heading', 'paragraph', 'table', 'table_row', 'figure', 'list', 'equation'"
    )
    page_number: Optional[int] = None
    reading_order: Optional[int] = None
    text_content: str
    equation_label: Optional[str] = Field(
        default=None,
        description="Equation label, e.g. '2' for equation (2)"
    )
    raw_latex: Optional[str] = Field(
        default=None,
        description="Raw LaTeX string for equation nodes"
    )
    metadata: DOMMetadata = Field(default_factory=DOMMetadata)
    children: List["DOMNode"] = Field(default_factory=list)

class DocumentDOM(BaseModel):
    """The root of the parsed document hierarchy."""
    document_id: str
    title: str = ""
    authors: List[str] = Field(default_factory=list)
    toc: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Extracted Table of Contents"
    )
    nodes: List[DOMNode] = Field(
        default_factory=list, 
        description="Top-level nodes (usually chapters or top headings)"
    )
    metadata: DOMMetadata = Field(default_factory=DOMMetadata)
