import logging
from typing import List, Optional
from src.services.ingestion.canonical.ast_schema import CanonicalDocument, ASTNode, NodeType

logger = logging.getLogger("hierarchy_engine")

class HierarchyEngine:
    def reconstruct(self, doc: CanonicalDocument) -> CanonicalDocument:
        """
        Reconstructs the hierarchical structure of a flat list of nodes.
        Returns the updated CanonicalDocument with a nested tree.
        """
        logger.info(f"Reconstructing hierarchy for document {doc.document_id}")
        
        if not doc.nodes:
            return doc
            
        flat_nodes = doc.nodes
        tree_nodes: List[ASTNode] = []
        
        # Simple stack-based approach
        # A stack stores nodes representing the path to the root
        stack: List[ASTNode] = []
        
        for node in flat_nodes:
            # We consider SECTION to be a heading that defines hierarchy
            if node.type == NodeType.SECTION:
                # If level is missing, guess it from text (e.g., "1.1 ")
                level = self._guess_level(node)
                node.level = level
                
                # Pop from stack until we find a parent with a strictly smaller level (i.e. higher in hierarchy)
                while stack and (stack[-1].level is None or stack[-1].level >= level):
                    stack.pop()
                    
                if stack:
                    parent = stack[-1]
                    node.parent_id = parent.id
                    parent.children.append(node)
                else:
                    tree_nodes.append(node)
                    
                stack.append(node)
            else:
                # Attach to current section if any, otherwise root
                if stack:
                    parent = stack[-1]
                    node.parent_id = parent.id
                    parent.children.append(node)
                else:
                    tree_nodes.append(node)
                    
        doc.nodes = tree_nodes
        return doc
        
    def _guess_level(self, node: ASTNode) -> int:
        if node.level is not None:
            return node.level
            
        text = node.text_content.strip()
        import re
        m = re.match(r'^(\d+(?:\.\d+)*)\s+', text)
        if m:
            section_num = m.group(1)
            dot_count = section_num.count(".")
            return dot_count + 1
            
        # Default to level 1 if we can't guess
        return 1
