import logging
from typing import List, Dict, Any
from src.infrastructure.model_factory import NLPModelFactory
from src.services.ingestion.canonical.ast_schema import ASTNode, NodeType

logger = logging.getLogger("relation_extractor")

class RelationExtractor:
    def __init__(self):
        pass
        
    async def extract_relations(self, nodes: List[ASTNode], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts relationships between entities using AST structure and spaCy.
        Returns a list of dicts: {"source": str, "target": str, "relation": str, "confidence": float, "method": str}
        """
        relations = []
        
        # Build map of node_id -> entities in that node
        node_to_entities = {}
        for ent in entities:
            # ent has surface_forms and source_node_ids (which is a list)
            for node_id in ent.get("source_node_ids", []):
                if node_id not in node_to_entities:
                    node_to_entities[node_id] = []
                node_to_entities[node_id].append(ent)
                
        # 1. Structural Rules (High Confidence)
        # E.g. If Section heading has an entity, and paragraph has an entity -> EXPLAINS or RELATED_TO
        # Note: We assume the tree was built in ast_builder and children are populated.
        def traverse_structural(node):
            if node.type == NodeType.SECTION:
                section_entities = node_to_entities.get(node.id, [])
                
                # Check immediate children for entities
                for child in node.children:
                    child_entities = node_to_entities.get(child.id, [])
                    for parent_ent in section_entities:
                        for child_ent in child_entities:
                            if parent_ent["canonical_name"] != child_ent["canonical_name"]:
                                relations.append({
                                    "source": parent_ent["canonical_name"],
                                    "target": child_ent["canonical_name"],
                                    "relation": "EXPLAINS",
                                    "confidence": 0.9,
                                    "method": "structural"
                                })
            for child in node.children:
                traverse_structural(child)
                
        # For a flat list that might have children, we just find root nodes and traverse
        roots = [n for n in nodes if not n.parent_id]
        for r in roots:
            traverse_structural(r)
                                
        # 2. Sentence-level proximity & dependency parsing (Medium Confidence)
        try:
            nlp = NLPModelFactory.get_spacy()
            for node in nodes:
                if node.id not in node_to_entities or not node.text_content:
                    continue
                    
                node_ents = node_to_entities[node.id]
                if len(node_ents) < 2:
                    continue
                    
                doc = nlp(node.text_content)
                # Very basic co-occurrence inside the same sentence
                for sent in doc.sents:
                    sent_text = sent.text.lower()
                    sent_ents = [e for e in node_ents if any(form.lower() in sent_text for form in e.get("surface_forms", []))]
                    
                    if len(sent_ents) >= 2:
                        # Create pairwise relations
                        for i in range(len(sent_ents)):
                            for j in range(i + 1, len(sent_ents)):
                                e1 = sent_ents[i]
                                e2 = sent_ents[j]
                                if e1["canonical_name"] != e2["canonical_name"]:
                                    relations.append({
                                        "source": e1["canonical_name"],
                                        "target": e2["canonical_name"],
                                        "relation": "RELATED_TO",
                                        "confidence": 0.6,
                                        "method": "spacy_cooccurrence"
                                    })
        except Exception as e:
            logger.warning(f"spaCy relation extraction skipped/failed: {e}")
            
        # Deduplicate
        unique_relations = {}
        for rel in relations:
            key = (rel["source"], rel["target"], rel["relation"])
            if key not in unique_relations or rel["confidence"] > unique_relations[key]["confidence"]:
                unique_relations[key] = rel
                
        return list(unique_relations.values())
