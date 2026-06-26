import logging
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel
import google.generativeai as genai
from src.config.settings import settings
from src.services.ingestion.extraction.base import BaseEntityExtractor

logger = logging.getLogger("gemini_extractor")

class TopicEntity(BaseModel):
    name: str
    description: str

class ConceptEntity(BaseModel):
    name: str
    description: str
    depends_on: List[str]

class AlgorithmEntity(BaseModel):
    name: str
    complexity: str
    uses_formulas: List[str]

class FormulaEntity(BaseModel):
    name: str
    expression: str
    description: str

class TechnologyEntity(BaseModel):
    name: str
    description: str

class BookEntity(BaseModel):
    title: str
    author: str

class PaperEntity(BaseModel):
    title: str
    authors: str
    year: int

class RelationshipEntity(BaseModel):
    from_entity: str
    to_entity: str
    relation: str

class ExtractedEntities(BaseModel):
    topics: List[TopicEntity]
    concepts: List[ConceptEntity]
    algorithms: List[AlgorithmEntity]
    formulas: List[FormulaEntity]
    technologies: List[TechnologyEntity]
    books: List[BookEntity]
    papers: List[PaperEntity]
    relationships: List[RelationshipEntity]

class GeminiEntityExtractor(BaseEntityExtractor):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)

    async def extract(self, chunks: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts entities using Gemini structured output.
        Batches chunks to avoid context limits and rate limits.
        """
        all_entities = {
            "topics": [], "concepts": [], "algorithms": [], "formulas": [],
            "technologies": [], "books": [], "papers": [], "relationships": []
        }
        
        # Batch size of 5 chunks
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_text = "\n\n---\n\n".join(batch_chunks)
            
            prompt = f"""
            You are an expert academic knowledge graph extractor. 
            Extract educational entities from the following text chunks.
            
            Document Context:
            Title: {context.get('title', 'Unknown')}
            Course: {context.get('course_code', 'Unknown')}
            Type: {context.get('doc_type', 'Unknown')}
            
            Text Chunks:
            {batch_text}
            """
            
            try:
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedEntities,
                        temperature=0.1
                    )
                )
                
                import json
                try:
                    result = json.loads(response.text)
                    for key in all_entities:
                        if key in result and result[key]:
                            all_entities[key].extend(result[key])
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON from Gemini: {je}")
                    
            except Exception as e:
                logger.error(f"Failed to extract entities for batch {i}: {e}")
                
            # Rate limiting delay
            if i + batch_size < len(chunks):
                await asyncio.sleep(1.0)
                
        # Deduplicate and normalize
        return self._normalize_entities(all_entities)
        
    def _normalize_entities(self, entities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        normalized = {}
        for key, entity_list in entities.items():
            seen = set()
            unique_list = []
            for item in entity_list:
                # Determine primary key (name or title or from/to)
                if "name" in item:
                    pk = item["name"].lower().strip()
                elif "title" in item:
                    pk = item["title"].lower().strip()
                elif "from_entity" in item:
                    pk = f"{item.get('from_entity', '')}-{item.get('to_entity', '')}-{item.get('relation', '')}".lower().strip()
                else:
                    pk = str(item)
                    
                if pk not in seen:
                    seen.add(pk)
                    unique_list.append(item)
            normalized[key] = unique_list
            
        return normalized
