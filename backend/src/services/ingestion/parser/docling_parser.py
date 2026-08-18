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
        
        import base64
        def extract_base64_uris(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "uri" and isinstance(v, str) and v.startswith("data:image/"):
                        try:
                            # Extract base64
                            header, encoded = v.split(",", 1)
                            img_bytes = base64.b64decode(encoded)
                            filename = f"extracted_{uuid.uuid4().hex[:8]}.png"
                            key = self.artifact_manager.asset_key(filename)
                            self.artifact_manager.s3.upload_image(key, img_bytes)
                            obj[k] = key  # Store S3 key instead of base64
                        except Exception as e:
                            logger.error(f"Error extracting base64 image: {e}")
                            obj[k] = "[ERROR EXTRACTING]"
                    else:
                        extract_base64_uris(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_base64_uris(item)
                    
        extract_base64_uris(raw_output)
        self.artifact_manager.upload_json(self.artifact_manager.parser_key("docling"), {"raw": raw_output})
        
        # 1. Export native markdown and save as document.md
        markdown_content = docling_doc.export_to_markdown()
        self.artifact_manager.upload_text(self.artifact_manager.prefix() + "/document.md", markdown_content)
        
        # 2. Extract page renders and save dimensions
        pages_manifest = {}
        if hasattr(result, 'pages') and result.pages:
            from io import BytesIO
            for page_info in result.pages:
                page_no = page_info.page_no
                if hasattr(page_info, 'image') and page_info.image:
                    # Save the image
                    img_byte_arr = BytesIO()
                    page_info.image.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    self.artifact_manager.s3.upload_image(self.artifact_manager.page_key(page_no), img_bytes)
                
                # Save dimensions
                if hasattr(page_info, 'size'):
                    pages_manifest[str(page_no)] = {
                        "width": page_info.size.width,
                        "height": page_info.size.height
                    }
            if pages_manifest:
                self.artifact_manager.upload_json(self.artifact_manager.prefix() + "/pages_manifest.json", pages_manifest)
        
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
        stack = [] # (level, node)
        
        # docling_doc is a docling.datamodel.document.Document
        from docling.datamodel.document import DocItemLabel
        
        # Build a hierarchical tree based on item level
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
                source=source,
                children=[]
            )
            
            # Extract image for figures
            if node_type == NodeType.FIGURE and hasattr(item, "get_image"):
                try:
                    pil_img = item.get_image(docling_doc)
                    if pil_img:
                        from io import BytesIO
                        img_byte_arr = BytesIO()
                        pil_img.save(img_byte_arr, format='PNG')
                        filename = f"figure_{node.id}.png"
                        key = self.artifact_manager.asset_key(filename)
                        self.artifact_manager.s3.upload_image(key, img_byte_arr.getvalue())
                        node.image_s3_key = key
                except Exception as e:
                    logger.warning(f"Failed to extract image for FIGURE node {node.id}: {e}")
            
            while stack and stack[-1][0] >= level:
                stack.pop()
                
            if stack:
                parent_node = stack[-1][1]
                node.parent_id = parent_node.id
                parent_node.children.append(node)
            else:
                canonical_nodes.append(node)
                
            stack.append((level, node))
            
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
