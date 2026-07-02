import logging
from typing import Dict, Any, List
from src.infrastructure.model_factory import NLPModelFactory

logger = logging.getLogger("spacy_relation_extractor")

class SpacyRelationExtractor:
    def __init__(self):
        pass
        
    async def extract_relations(self, chunks: List[str], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Uses spaCy dependency parsing and rule-based logic to extract relationships
        between the provided entities within the text chunks.
        """
        try:
            nlp = NLPModelFactory.get_spacy()
        except Exception as e:
            logger.error(f"Failed to load spaCy: {e}")
            return []

        relations = []
        # Create a fast lookup for entities
        entity_texts = {ent["canonical_name"].lower(): ent for ent in entities if "canonical_name" in ent}
        
        for chunk in chunks:
            doc = nlp(chunk)
            
            # Very basic rule-based relationship extraction using dependency parsing
            # E.g., looking for Subject-Verb-Object (SVO) triplets
            for token in doc:
                if token.dep_ == "ROOT" and token.pos_ == "VERB":
                    subj = None
                    obj = None
                    
                    for child in token.children:
                        if child.dep_ in ["nsubj", "nsubjpass"]:
                            subj = child
                        elif child.dep_ in ["dobj", "pobj", "attr"]:
                            obj = child
                            
                    if subj and obj:
                        # Check if subj and obj are in our extracted entities
                        # In a real implementation, we'd look at subtree or noun chunks
                        subj_text = subj.text.lower()
                        obj_text = obj.text.lower()
                        
                        subj_ent = entity_texts.get(subj_text)
                        obj_ent = entity_texts.get(obj_text)
                        
                        if subj_ent and obj_ent:
                            relations.append({
                                "source": subj_ent["canonical_name"],
                                "target": obj_ent["canonical_name"],
                                "type": token.lemma_.upper(),
                                "source_label": subj_ent["label"],
                                "target_label": obj_ent["label"]
                            })
                            
        # Note: This is a fallback-friendly design. If relations are sparse or confidence is low,
        # we can pass the chunk to an LLM for deeper extraction.
        
        return relations
