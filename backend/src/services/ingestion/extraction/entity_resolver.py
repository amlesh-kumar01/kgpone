import logging
from typing import Dict, Any, List

logger = logging.getLogger("entity_resolver")

class EntityResolver:
    def __init__(self, score_cutoff: float = 85.0):
        self.score_cutoff = score_cutoff
        
    def resolve(self, extracted_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Uses RapidFuzz to resolve and merge similar entities.
        Adds a 'canonical_name' to each entity.
        """
        try:
            from rapidfuzz import process, fuzz
        except ImportError:
            logger.error("rapidfuzz is not installed. Returning unresolved entities.")
            for ent in extracted_entities:
                ent["canonical_name"] = ent["text"]
                ent["surface_forms"] = [ent["text"]]
                ent["source_node_ids"] = [ent.get("source_node_id")] if ent.get("source_node_id") else []
            return extracted_entities

        resolved_entities = []
        canonical_map = {} # canonical_name -> entity dict
        
        for ent in extracted_entities:
            text = ent["text"]
            label = ent["label"]
            
            # Simple normalization
            norm_text = text.strip().title()
            
            if not canonical_map:
                ent["canonical_name"] = norm_text
                ent["surface_forms"] = {text}
                ent["source_node_ids"] = {ent.get("source_node_id")} if ent.get("source_node_id") else set()
                canonical_map[norm_text] = ent
                continue
                
            # Try to match with existing canonical names
            existing_names = list(canonical_map.keys())
            
            # ExtractOne returns (match, score, index)
            match_result = process.extractOne(norm_text, existing_names, scorer=fuzz.WRatio)
            
            if match_result and match_result[1] >= self.score_cutoff:
                matched_name = match_result[0]
                existing_ent = canonical_map[matched_name]
                
                # We found a match, so they are the same entity
                existing_ent["surface_forms"].add(text)
                if ent.get("source_node_id"):
                    existing_ent["source_node_ids"].add(ent.get("source_node_id"))
                
                # Merge scores or keep highest
                if ent.get("score", 0) > existing_ent.get("score", 0):
                    existing_ent["score"] = ent.get("score")
                    
            else:
                # No match, it's a new canonical entity
                ent["canonical_name"] = norm_text
                ent["surface_forms"] = {text}
                ent["source_node_ids"] = {ent.get("source_node_id")} if ent.get("source_node_id") else set()
                canonical_map[norm_text] = ent
                
        # Convert sets to lists
        for ent in canonical_map.values():
            ent["surface_forms"] = list(ent.get("surface_forms", []))
            ent["source_node_ids"] = list(ent.get("source_node_ids", []))
            
        return list(canonical_map.values())
