import logging
import asyncio
from typing import Optional
from src.services.ingestion.canonical.ast_schema import CanonicalDocument
from src.services.ingestion.artifact_manager import ArtifactManager
from src.services.ingestion.parser.docling_parser import DoclingParser
from src.services.ingestion.parser.llama_parser import LlamaParserImpl
from src.services.ingestion.quality.quality_evaluator import QualityEvaluator, QualityReport
from src.services.ingestion.hierarchy.hierarchy_engine import HierarchyEngine

logger = logging.getLogger("ast_builder")

class ASTBuilder:
    def __init__(self, artifact_manager: ArtifactManager, llama_parser: LlamaParserImpl):
        self.artifact_manager = artifact_manager
        self.docling_parser = DoclingParser(artifact_manager)
        self.llama_parser = llama_parser
        self.quality_evaluator = QualityEvaluator()
        self.hierarchy_engine = HierarchyEngine()
        
    async def build(self, file_path: str, parsing_instructions: Optional[str] = None) -> CanonicalDocument:
        """
        Runs parsers, evaluates quality, routes accordingly, and builds the final Canonical AST.
        """
        # 1. Try Docling
        try:
            docling_doc = await asyncio.to_thread(self.docling_parser.parse, file_path)
            report = self.quality_evaluator.evaluate(docling_doc)
            docling_doc.provenance.quality_score = report.score
            
            if not report.needs_fallback:
                logger.info(f"Docling parse succeeded with score {report.score}")
                best_doc = docling_doc
            else:
                logger.warning(f"Docling fallback triggered: {report.fallback_reason}")
                best_doc = await self._run_llama_fallback(file_path, parsing_instructions, docling_doc, report)
        except Exception as e:
            logger.error(f"Docling parser failed completely: {e}")
            logger.info("Falling back to LlamaParse.")
            best_doc = await self._run_llama_fallback(file_path, parsing_instructions, None, None)
            
        # 2. Reconstruct Hierarchy
        best_doc = self.hierarchy_engine.reconstruct(best_doc)
        
        # 3. Save Canonical Artifacts
        dumped_data = best_doc.model_dump(mode="json")
        self.artifact_manager.upload_json(self.artifact_manager.canonical_key(), dumped_data)
        
        # Update manifest
        self.artifact_manager.update_manifest({
            "artifacts": {
                "canonical": self.artifact_manager.canonical_key(),
                "parsers": {
                    best_doc.provenance.parser_used: self.artifact_manager.parser_key(best_doc.provenance.parser_used)
                }
            }
        })
        
        return best_doc
        
    async def _run_llama_fallback(
        self, 
        file_path: str, 
        instructions: Optional[str],
        docling_doc: Optional[CanonicalDocument],
        docling_report: Optional[QualityReport]
    ) -> CanonicalDocument:
        dom = await self.llama_parser.parse(file_path, instructions)
        
        # Save LlamaParse artifact to S3
        self.artifact_manager.upload_json(self.artifact_manager.parser_key("llamaparse"), dom.model_dump(mode="json"))
        
        llama_doc = self.llama_parser.to_canonical(dom)
        
        # Evaluate LlamaParse
        llama_report = self.quality_evaluator.evaluate(llama_doc)
        llama_doc.provenance.quality_score = llama_report.score
        
        # Compare and pick best
        if docling_doc and docling_report and docling_report.score > llama_report.score:
            logger.info("Docling fallback yielded lower score. Sticking with Docling.")
            return docling_doc
            
        logger.info(f"LlamaParse chosen with score {llama_report.score}")
        return llama_doc
