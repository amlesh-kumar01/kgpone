import unittest
import os
import sys
from pathlib import Path

# Add project src to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.services.ingestion.ingestion_service import IngestionService
from src.services.graph.prerequisite_service import PrerequisiteService
from src.services.rag.retrieval_service import RetrievalService
from src.services.rag.rerank_service import RerankService
from src.services.rag.citation_service import CitationService
from src.services.rag.answer_service import AnswerService
from src.config.qdrant import QdrantRepo
from src.config.neo4j import Neo4jRepo

class TestRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Force services into local/fallback test mode if external DBs aren't up
        # This makes the tests 100% stable regardless of host state
        cls.qdrant_repo = QdrantRepo()
        cls.neo4j_repo = Neo4jRepo()
        
        cls.ingestor = IngestionService()
        cls.prereq_service = PrerequisiteService()
        cls.retrieval_service = RetrievalService()
        cls.rerank_service = RerankService()
        cls.citation_service = CitationService()
        cls.answer_service = AnswerService()

    def test_complete_rag_workflow(self):
        # 1. Test Ingestion with a sample course material
        sample_markdown = (
            "# Lecture 4: Heuristic Search Techniques\n"
            "In this class we introduce Heuristic search algorithms.\n"
            "## A* Heuristic Search\n"
            "A* Search uses an evaluation function f(n) = g(n) + h(n), where g(n) is the cost from start node "
            "and h(n) is the heuristic estimation to the target. It is used to compute optimal paths.\n"
            "--- (page change)\n"
            "## Dijkstra Algorithm\n"
            "Dijkstra is a special case of A* where h(n) = 0. It relaxes edges sequentially to find the shortest path."
        )
        
        file_id = "test-doc-id-123"
        metadata = {
            "title": "Lecture 4 Notes",
            "course_code": "CSE301",
            "academic_year": "3rd Year"
        }
        
        # Ingest
        success = self.ingestor.ingest_parsed_markdown(file_id, sample_markdown, metadata)
        self.assertTrue(success, "Ingestion failed")

        # 2. Test Prerequisite Diagnosis and Curriculum Time Travel
        # We query for Heuristics. The system should traverse backwards to Discrete Mathematics (MTH201)
        diagnosis = self.prereq_service.diagnose_missing_prerequisites(
            query="Tell me about A* heuristics and optimization.",
            active_course_code="CSE301"
        )
        
        self.assertTrue(diagnosis["has_missing_prerequisites"], "Prerequisite diagnosis should find missing foundational concepts")
        self.assertIn("Graph Theory Basics", diagnosis["missing_prerequisites"])
        
        # Verify graph visualization output format for frontend
        vis_graph = diagnosis["graph_visualization"]
        self.assertIn("nodes", vis_graph)
        self.assertIn("edges", vis_graph)
        self.assertTrue(len(vis_graph["nodes"]) > 0)
        self.assertTrue(len(vis_graph["edges"]) > 0)

        # 3. Test Retrieval Service
        retrieved_result = self.retrieval_service.retrieve_context(
            query="Explain Dijkstra pathfinding and prerequisites.",
            course_code="CSE301"
        )
        
        self.assertTrue(len(retrieved_result["retrieved_chunks"]) > 0, "No chunks retrieved")
        
        # 4. Test Reranking
        ranked_chunks = self.rerank_service.rerank_chunks(
            query="Explain Dijkstra pathfinding and prerequisites.",
            chunks=retrieved_result["retrieved_chunks"],
            top_n=3
        )
        self.assertTrue(len(ranked_chunks) <= 3)
        self.assertTrue(ranked_chunks[0]["final_score"] >= ranked_chunks[-1]["final_score"])

        # 5. Test Citations / Provenance
        citations = self.citation_service.format_citations(ranked_chunks)
        self.assertEqual(len(citations), len(ranked_chunks))
        self.assertEqual(citations[0]["citation_id"], "CIT-1")
        self.assertIsNotNone(citations[0]["confidence"])

        # 6. Test Answer Generation
        answer = self.answer_service.generate_answer(
            query="Explain Dijkstra pathfinding and prerequisites.",
            ranked_chunks=ranked_chunks,
            citations=citations
        )
        self.assertIsNotNone(answer)
        self.assertTrue(len(answer) > 0)
        print(f"Generated Grounded Test Answer:\n{answer}")

if __name__ == "__main__":
    unittest.main()
