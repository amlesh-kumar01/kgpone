import asyncio
import json
import logging
from typing import AsyncGenerator, Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from src.repositories.qdrant.vector_repository import QdrantRepository
from src.schemas.query_schema import QueryRequest

logger = logging.getLogger("map_reduce_service")

# Map Prompt: Evaluates a batch of chunks against the user's query
_MAP_SYSTEM_PROMPT = """You are an expert academic research assistant.
Your task is to extract relevant information from a batch of document chunks to answer the user's query.
If the chunks contain no relevant information, output: "NO_RELEVANT_INFO".
Otherwise, extract the exact information requested by the user. Do not make up answers.
Ensure you retain important context, details, and exact quotes if applicable.
"""

# Reduce Prompt: Synthesizes all map results into a final answer
_REDUCE_SYSTEM_PROMPT = """You are an expert academic synthesizer.
You have been provided with extracted information from various parts of a document.
Your task is to synthesize this information into a comprehensive, deduplicated, and cohesive final answer to the user's query.
Format the output elegantly using markdown.
If the extracted information contains "NO_RELEVANT_INFO" and nothing else, politely inform the user that the document does not contain the requested information.
"""

class MapReduceService:
    def __init__(self, llm: BaseChatModel, vector_repo: QdrantRepository):
        self.llm = llm
        self.vector_repo = vector_repo
        # Cap concurrent map requests to avoid hitting rate limits (e.g. Gemini 15 RPM)
        self.semaphore = asyncio.Semaphore(3)

    async def _map_batch(self, query: str, batch: list[dict], batch_idx: int) -> str:
        """Runs the map step for a batch of chunks."""
        async with self.semaphore:
            logger.info(f"[MapReduce] Mapping batch {batch_idx+1} ({len(batch)} chunks)...")
            
            # Combine chunk texts
            context = ""
            for i, chunk in enumerate(batch):
                context += f"\n--- Chunk {i+1} ---\n{chunk.get('text', '')}\n"
                
            messages = [
                SystemMessage(content=_MAP_SYSTEM_PROMPT),
                HumanMessage(content=f"Query: {query}\n\nDocument Context:{context}")
            ]
            
            try:
                response = await self.llm.ainvoke(messages)
                result = response.content
                if not isinstance(result, str):
                    result = str(result)
                return result
            except Exception as e:
                logger.error(f"[MapReduce] Error in map batch {batch_idx+1}: {e}")
                return "NO_RELEVANT_INFO"

    async def execute_stream(
        self, 
        query: str, 
        document_id: str, 
        req: QueryRequest
    ) -> AsyncGenerator[str, None]:
        """
        Executes the map-reduce pipeline across all chunks of a document,
        streaming the final reduced output back to the client.
        """
        logger.info(f"[MapReduce] Starting Deep Research for doc={document_id}")
        
        # 1. Fetch all chunks for the document
        chunks = await self.vector_repo.get_chunks_by_document_id(
            collection_name="kgpone_vectors", 
            document_id=document_id
        )
        
        if not chunks:
            yield f"data: {json.dumps({'content': 'No content found for this document.', 'type': 'content'})}\n\n"
            return
            
        logger.info(f"[MapReduce] Found {len(chunks)} chunks for doc={document_id}. Batching...")
        
        # 2. Batch chunks (e.g. 10 chunks per batch) to optimize tokens vs rate limits
        batch_size = 10
        batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
        
        yield f"data: {json.dumps({'content': f'\\n*Initializing Deep Research map-reduce over {len(chunks)} sections in {len(batches)} batches...*\\n\\n', 'type': 'content'})}\n\n"
        
        # 3. Execute Map Step Concurrently
        map_tasks = [
            self._map_batch(query, batch, i)
            for i, batch in enumerate(batches)
        ]
        
        map_results = await asyncio.gather(*map_tasks)
        
        # Filter out empty results
        useful_results = [r for r in map_results if r and "NO_RELEVANT_INFO" not in r]
        
        if not useful_results:
            yield f"data: {json.dumps({'content': 'I scanned the entire document but could not find information relevant to your query.', 'type': 'content'})}\n\n"
            return
            
        yield f"data: {json.dumps({'content': f'\\n*Map phase complete. Synthesizing {len(useful_results)} extractions...*\\n\\n', 'type': 'content'})}\n\n"
        
        # 4. Execute Reduce Step (Streaming)
        combined_extractions = "\n\n======================\n\n".join(useful_results)
        
        reduce_messages = [
            SystemMessage(content=_REDUCE_SYSTEM_PROMPT),
            HumanMessage(content=f"Original Query: {query}\n\nExtracted Information:\n{combined_extractions}")
        ]
        
        try:
            async for chunk in self.llm.astream(reduce_messages):
                content = chunk.content
                if content:
                    yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"
        except Exception as e:
            logger.error(f"[MapReduce] Error during reduce streaming: {e}")
            yield f"data: {json.dumps({'content': f'\\n\\n[Error synthesizing results: {e}]', 'type': 'content'})}\n\n"
