import logging
import re
import uuid
from typing import List, Dict, Any
from src.services.ingestion.canonical.ast_schema import ASTNode, NodeType

logger = logging.getLogger("formula_extractor")

class FormulaExtractor:
    def __init__(self):
        # Matches inline LaTeX between single $ or double $$
        self.inline_regex = re.compile(r'(?<!\$)\$([^$]+)\$(?!\$)')
        self.block_regex = re.compile(r'\$\$([^$]+)\$\$')
        self.env_regex = re.compile(r'\\begin\{(equation|align|eqnarray\*?|math|displaymath)\}(.*?)\\end\{\1\}', re.DOTALL)
        
    def extract(self, nodes: List[ASTNode], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts standalone and inline equations from AST nodes.
        """
        formulas = []
        
        for idx, node in enumerate(nodes):
            if node.type == NodeType.EQUATION:
                formulas.append({
                    "id": str(uuid.uuid4()),
                    "latex": node.latex if node.latex else node.text_content,
                    "equation_label": node.equation_label,
                    "source_node_id": node.id,
                    "source_page": node.source.page_start if node.source else None,
                    "variables": self._extract_variables(node, nodes, idx)
                })
            elif node.type == NodeType.PARAGRAPH and node.text_content:
                # Search for inline math
                text = node.text_content
                
                # Check blocks first
                for match in self.block_regex.finditer(text):
                    formulas.append({
                        "id": str(uuid.uuid4()),
                        "latex": match.group(1).strip(),
                        "equation_label": None,
                        "source_node_id": node.id,
                        "source_page": node.source.page_start if node.source else None,
                        "variables": self._extract_variables(node, nodes, idx)
                    })
                    
                # Check standard environments
                for match in self.env_regex.finditer(text):
                    formulas.append({
                        "id": str(uuid.uuid4()),
                        "latex": match.group(2).strip(),
                        "equation_label": None,
                        "source_node_id": node.id,
                        "source_page": node.source.page_start if node.source else None,
                        "variables": self._extract_variables(node, nodes, idx)
                    })
                    
                # Check inline
                for match in self.inline_regex.finditer(text):
                    latex = match.group(1).strip()
                    if len(latex) > 2: # Ignore single variables like $x$ usually not a formula
                        formulas.append({
                            "id": str(uuid.uuid4()),
                            "latex": latex,
                            "equation_label": None,
                            "source_node_id": node.id,
                            "source_page": node.source.page_start if node.source else None,
                            "variables": [] # Inline math variable extraction is too noisy without LLM
                        })
                        
        return {"formulas": formulas}
        
    def _extract_variables(self, node: ASTNode, all_nodes: List[ASTNode], current_idx: int) -> List[Dict[str, str]]:
        """
        Heuristically extracts variables from surrounding context.
        E.g., looks for 'where x is ...' or 'y denotes ...'
        """
        variables = []
        context_text = ""
        
        # Get ~2 nodes before and after
        start = max(0, current_idx - 2)
        end = min(len(all_nodes), current_idx + 3)
        
        for i in range(start, end):
            if all_nodes[i].type == NodeType.PARAGRAPH and all_nodes[i].text_content:
                context_text += " " + all_nodes[i].text_content
                
        # A simple regex for "where <var> is <meaning>"
        # "where $x$ is the distance"
        where_match = re.search(r'where\s+\$([a-zA-Z0-9_]+)\$\s+is\s+(the\s+)?([^,.]+)', context_text, re.IGNORECASE)
        if where_match:
            variables.append({
                "symbol": where_match.group(1),
                "meaning": where_match.group(3).strip(),
                "unit": None
            })
            
        return variables
