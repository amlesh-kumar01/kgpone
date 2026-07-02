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
                canonical_map[norm_text] = ent
                continue
                
            # Try to match with existing canonical names
            existing_names = list(canonical_map.keys())
            
            # ExtractOne returns (match, score, index)
            match_result = process.extractOne(norm_text, existing_names, scorer=fuzz.WRatio)
            
            if match_result and match_result[1] >= self.score_cutoff:
                matched_name = match_result[0]
                # We found a match, so they are the same entity
                ent["canonical_name"] = matched_name
                
                # Merge scores or keep highest
                existing_ent = canonical_map[matched_name]
                if ent.get("score", 0) > existing_ent.get("score", 0):
                    existing_ent["score"] = ent.get("score")
                    
            else:
                # No match, it's a new canonical entity
                ent["canonical_name"] = norm_text
                canonical_map[norm_text] = ent
                
        # Return unique canonical entities
        return list(canonical_map.values())
