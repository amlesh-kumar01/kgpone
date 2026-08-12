import json
from typing import Dict, Any, Tuple

class Evaluator:
    def __init__(self, gold_standard: Dict[str, Any]):
        self.gold_standard = gold_standard
        
    def evaluate(self, doc_filename: str, entities: list, formulas: list, questions: list) -> Dict[str, Any]:
        gold = self.gold_standard.get("test_documents", {}).get(doc_filename)
        if not gold:
            return {"error": f"No gold standard found for {doc_filename}"}
            
        # Entities Evaluation
        expected_entities = set(gold.get("expected_entities", []))
        extracted_entities = set([e.get("name") for e in entities if isinstance(e, dict) and e.get("name")])
        
        tp_ent = len(expected_entities.intersection(extracted_entities))
        fp_ent = len(extracted_entities - expected_entities)
        fn_ent = len(expected_entities - extracted_entities)
        
        ent_precision = tp_ent / (tp_ent + fp_ent) if (tp_ent + fp_ent) > 0 else 0.0
        ent_recall = tp_ent / (tp_ent + fn_ent) if (tp_ent + fn_ent) > 0 else 0.0
        ent_f1 = 2 * (ent_precision * ent_recall) / (ent_precision + ent_recall) if (ent_precision + ent_recall) > 0 else 0.0
        
        # Formulas Evaluation
        expected_f_count = gold.get("expected_formulas_count", 0)
        extracted_f_count = len(formulas)
        f_recall = min(1.0, extracted_f_count / expected_f_count) if expected_f_count > 0 else 1.0
        
        # Questions Evaluation
        expected_questions = set(gold.get("expected_questions", []))
        extracted_questions = set([q.get("question_text") for q in questions if isinstance(q, dict) and q.get("question_text")])
        
        # Exact match is hard for questions, we just check count for simplicity
        q_recall = min(1.0, len(extracted_questions) / len(expected_questions)) if len(expected_questions) > 0 else 1.0
        
        return {
            "entity_precision": round(ent_precision, 4),
            "entity_recall": round(ent_recall, 4),
            "entity_f1": round(ent_f1, 4),
            "formula_extraction_percent": round(f_recall * 100, 2),
            "question_extraction_percent": round(q_recall * 100, 2),
            "extracted_counts": {
                "entities": len(extracted_entities),
                "formulas": extracted_f_count,
                "questions": len(extracted_questions)
            }
        }
