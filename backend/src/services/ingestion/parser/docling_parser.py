import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from src.services.ingestion.canonical.ast_schema import (
    NodeType, NodeSource, ASTNode, ParserProvenance, CanonicalDocument
)
from src.infrastructure.model_factory import NLPModelFactory
from src.services.ingestion.artifact_manager import ArtifactManager

logger = logging.getLogger("docling_parser")

class DoclingParser:
    def __init__(self, artifact_manager: ArtifactManager):
        self.artifact_manager = artifact_manager
        self.doc_id = artifact_manager.document_id
        
    def parse(self, file_path: str) -> CanonicalDocument:
        logger.info(f"Docling: parsing {file_path}")
        converter = NLPModelFactory.get_docling()
        
        result = converter.convert(file_path)
        docling_doc = result.document
        
        # Save raw docling output
        raw_output = docling_doc.export_to_dict()
        self.artifact_manager.upload_json(self.artifact_manager.parser_key("docling"), raw_output)
        
        # Translate to CanonicalDocument
        nodes = self._translate_docling_to_ast(docling_doc)
        
        provenance = ParserProvenance(
            parser_used="docling",
            parser_version="2.0",
            quality_score=0.0, # Will be set by QualityEvaluator
            processing_timestamp=datetime.utcnow()
        )
        
        canonical_doc = CanonicalDocument(
            document_id=self.doc_id,
            nodes=nodes,
            provenance=provenance
        )
        return canonical_doc

    def _translate_docling_to_ast(self, docling_doc: Any) -> List[ASTNode]:
        """Maps docling native AST to Canonical AST."""
        canonical_nodes = []
        
        # docling_doc is a docling.datamodel.document.Document
        from docling.datamodel.document import DocItemLabel
        
        # We'll just build a flat list. Hierarchy Engine will assemble the tree later.
        for item, level in docling_doc.iterate_items():
            node_type = self._map_docling_label(item.label)
            
            bbox = None
            page_start = None
            page_end = None
            if hasattr(item, "prov") and item.prov:
                # prov is a list of ProvenanceItem
                prov = item.prov[0]
                page_start = prov.page_no
                page_end = prov.page_no
                if hasattr(prov, "bbox"):
                    bbox = [prov.bbox.l, prov.bbox.t, prov.bbox.r, prov.bbox.b]
            
            source = NodeSource(
                document_id=self.doc_id,
                page_start=page_start,
                page_end=page_end,
                bbox=bbox,
                parser="docling",
                parser_version="2.0"
            )
            
            node = ASTNode(
                id=str(uuid.uuid4()),
                type=node_type,
                level=level if level else None,
                text_content=item.text if hasattr(item, "text") else "",
                source=source
            )
            canonical_nodes.append(node)
            
        return canonical_nodes

    def _map_docling_label(self, label: Any) -> NodeType:
        from docling.datamodel.document import DocItemLabel
        if label in (DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER):
            return NodeType.SECTION
        elif label == DocItemLabel.PARAGRAPH:
            return NodeType.PARAGRAPH
        elif label == DocItemLabel.LIST_ITEM:
            return NodeType.LIST_ITEM
        elif label == DocItemLabel.TABLE:
            return NodeType.TABLE
        elif label == DocItemLabel.PICTURE:
            return NodeType.FIGURE
        elif label == DocItemLabel.FORMULA:
            return NodeType.EQUATION
        elif label == DocItemLabel.CODE:
            return NodeType.CODE_BLOCK
        return NodeType.PARAGRAPH
