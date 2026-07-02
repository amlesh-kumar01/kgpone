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
        entity_resolver = None,
        relation_extractor = None,
        graph_builder = None
    ):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.entity_extractor = entity_extractor
        self.entity_resolver = entity_resolver
        self.relation_extractor = relation_extractor
        self.graph_builder = graph_builder

    async def process_document(self, file_path: str, metadata_base: dict, parsing_instructions: str | None = None):
        """
        Executes the full pipeline: Parse -> DOM -> Chunk -> Extract -> Resolve -> Embed -> Store.
        `metadata_base` should contain things like course_offering_id, document_id, title, etc.
        """
        logger.info(f"Starting ingestion pipeline for {file_path}")
        
        # 1. Parse (ToC-aware DOM Creation)
        logger.info("Parsing document into DOM...")
        document_dom = await self.parser.parse(file_path, parsing_instructions=parsing_instructions)
        
        # Merge base metadata into the DOM for inheritance
        document_dom.metadata.document_id = metadata_base.get("document_id")
        document_dom.metadata.course_offering_id = metadata_base.get("course_offering_id")
        if metadata_base.get("title"):
            document_dom.title = metadata_base.get("title")
        
        # 2. Chunk (Hierarchical and Row-as-a-Chunk)
        logger.info("Chunking document DOM...")
        chunks = self.chunker.chunk(document_dom)
        
        if not chunks:
            logger.warning("No chunks generated from document.")
            return

        chunk_texts = [chunk["content"] for chunk in chunks]
        
        # 3. Extract & Resolve Entities
        resolved_entities = []
        relations = []
        doc_id = metadata_base.get("document_id")
        
        if self.entity_extractor and self.entity_resolver:
            logger.info("Extracting and resolving entities...")
            try:
                extraction_result = await self.entity_extractor.extract(chunk_texts, metadata_base)
                raw_entities = extraction_result.get("entities", [])
                
                # Resolve canonical names using RapidFuzz
                resolved_entities = self.entity_resolver.resolve(raw_entities)
                
                # Extract Relationships using spaCy
                if self.relation_extractor and resolved_entities:
                    logger.info("Extracting relationships...")
                    relations = await self.relation_extractor.extract_relations(chunk_texts, resolved_entities)
                    
            except Exception as e:
                logger.error(f"Entity/Relation extraction failed (continuing pipeline): {e}")

        # 4. Push to Knowledge Graph (Lean Storage)
        if self.graph_builder and doc_id:
            logger.info("Pushing lean ontology to Knowledge Graph...")
            try:
                # Store structural skeleton (ToC Headings, Tables)
                self.graph_builder.build_document_skeleton(doc_id, document_dom)
                # Store resolved entities and relations
                self.graph_builder.add_extracted_entities(doc_id, {"entities": resolved_entities, "relations": relations})
            except Exception as e:
                logger.error(f"Graph ingestion failed (continuing pipeline): {e}")

        # Prepare metadata for Qdrant (full text storage)
        metadata_list = []
        for chunk in chunks:
            # Merge base metadata with chunk-specific metadata
            meta = metadata_base.copy()
            chunk_meta = chunk.get("metadata", {})
            for k, v in chunk_meta.items():
                if v is not None:
                    meta[k] = v
            # CRITICAL: persist chunk_type and content into the Qdrant payload so the
            # retrieval service can do type-aware formatting and figure URL injection.
            meta["chunk_type"] = chunk.get("chunk_type", "text")
            meta["content"] = chunk.get("content", "")
            metadata_list.append(meta)

        # 5. Embed
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        vectors = await self.embedder.embed(chunk_texts)

        # 6. Store in Vector Database
        logger.info("Storing vectors in Qdrant...")
        await self.vector_store.upsert(self.collection_name, vectors, metadata_list)
        
        logger.info("Ingestion pipeline completed successfully.")
