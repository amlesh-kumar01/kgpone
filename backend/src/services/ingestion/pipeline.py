import logging
from src.services.ingestion.parser.base import BaseParser
from src.services.ingestion.chunking.base import BaseChunker
from src.services.ingestion.embedding.base import BaseEmbedder
from src.utils.interfaces import IVectorRepo

logger = logging.getLogger("ingestion_pipeline")

class IngestionPipeline:
    def __init__(
        self,
        parser: BaseParser,
        chunker: BaseChunker,
        embedder: BaseEmbedder,
        vector_store: IVectorRepo,
        collection_name: str = "documents",
        entity_extractor = None,
        graph_builder = None
    ):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.entity_extractor = entity_extractor
        self.graph_builder = graph_builder

    async def process_document(self, file_path: str, metadata_base: dict, parsing_instructions: str | None = None):
        """
        Executes the full pipeline: Parse -> Chunk -> Embed -> Store -> Extract Entities.
        `metadata_base` should contain things like course_offering_id, document_id, etc.
        """
        logger.info(f"Starting ingestion pipeline for {file_path}")
        
        # 1. Parse
        logger.info("Parsing document...")
        markdown_content = await self.parser.parse(file_path, parsing_instructions=parsing_instructions)
        
        # 2. Chunk
        logger.info("Chunking document...")
        chunks = self.chunker.chunk(markdown_content)
        
        if not chunks:
            logger.warning("No chunks generated from document.")
            return

        # Prepare metadata
        chunk_texts = []
        metadata_list = []
        for chunk in chunks:
            chunk_texts.append(chunk["content"])
            # Merge base metadata with chunk-specific metadata
            meta = metadata_base.copy()
            meta.update(chunk)
            metadata_list.append(meta)

        # 3. Embed
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        vectors = await self.embedder.embed(chunk_texts)

        # 4. Store
        logger.info("Storing vectors in Qdrant...")
        await self.vector_store.upsert(self.collection_name, vectors, metadata_list)
        
        # 5. Extract Entities (Optional)
        if self.entity_extractor and self.graph_builder:
            logger.info("Extracting entities for Knowledge Graph...")
            try:
                doc_id = metadata_base.get("document_id")
                extracted = await self.entity_extractor.extract(chunk_texts, metadata_base)
                if extracted and doc_id:
                    self.graph_builder.add_extracted_entities(doc_id, extracted)
            except Exception as e:
                logger.error(f"Entity extraction failed (continuing pipeline): {e}")

        logger.info("Ingestion pipeline completed successfully.")
