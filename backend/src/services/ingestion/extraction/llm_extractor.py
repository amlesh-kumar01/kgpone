import logging
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel
from src.infrastructure.llm_factory import LLMFactory
from src.services.ingestion.extraction.base import BaseEntityExtractor
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("llm_extractor")

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Using Optional fields and default_factory prevents LLM strict schema validation crashes
class TopicEntity(BaseModel):
    name: str = Field(description="Name of the topic")
    description: Optional[str] = Field(default=None, description="Detailed description")

class ConceptEntity(BaseModel):
    name: str
    description: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)

class AlgorithmEntity(BaseModel):
    name: str
    complexity: Optional[str] = None
    uses_formulas: List[str] = Field(default_factory=list)

class FormulaEntity(BaseModel):
    name: str
    expression: str
    description: Optional[str] = None

class TechnologyEntity(BaseModel):
    name: str
    description: Optional[str] = None

class BookEntity(BaseModel):
    title: str
    author: List[str] = Field(default_factory=list, description="List of authors")

class PaperEntity(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: Optional[int] = None

class RelationshipEntity(BaseModel):
    from_entity: str
    to_entity: str
    relation: str

class ExtractedEntities(BaseModel):
    topics: List[TopicEntity] = Field(default_factory=list, description="MUST be a list of objects")
    concepts: List[ConceptEntity] = Field(default_factory=list, description="MUST be a list of objects")
    algorithms: List[AlgorithmEntity] = Field(default_factory=list, description="MUST be a list of objects")
    formulas: List[FormulaEntity] = Field(default_factory=list, description="MUST be a list of objects")
    technologies: List[TechnologyEntity] = Field(default_factory=list, description="MUST be a list of objects")
    books: List[BookEntity] = Field(default_factory=list, description="MUST be a list of objects")
    papers: List[PaperEntity] = Field(default_factory=list, description="MUST be a list of objects")
    relationships: List[RelationshipEntity] = Field(default_factory=list, description="MUST be a list of objects")

class LLMEntityExtractor(BaseEntityExtractor):
    def __init__(self, model_name: str | None = None):
        self.factory = LLMFactory()
        try:
            llm = self.factory.get_llm(model_name)
            self.structured_llm = llm.with_structured_output(ExtractedEntities)
        except Exception as e:
            logger.error(f"Failed to initialize LLM with structured output: {e}")
            self.structured_llm = None
            
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert academic knowledge graph extractor. Extract educational entities from the text chunks provided by the user. Do not include any explanations, just the structured data."),
            ("user", "Document Context:\nTitle: {title}\nCourse: {course}\nType: {type}\n\nText Chunks:\n{text}")
        ])

    async def extract(self, chunks: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts entities using Langchain structured output.
        Batches chunks to avoid context limits and rate limits.
        """
        all_entities = {
            "topics": [], "concepts": [], "algorithms": [], "formulas": [],
            "technologies": [], "books": [], "papers": [], "relationships": []
        }
        
        if not self.structured_llm:
            return all_entities
            
        chain = self.prompt_template | self.structured_llm
        
        # Batch size of 5 chunks
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_text = "\n\n---\n\n".join(batch_chunks)
            
            try:
                result = await chain.ainvoke({
                    "title": context.get('title', 'Unknown'),
                    "course": context.get('course_code', 'Unknown'),
                    "type": context.get('doc_type', 'Unknown'),
                    "text": batch_text
                })
                
                # result is an ExtractedEntities object
                if result:
                    res_dict = result.dict()
                    for key in all_entities:
                        if key in res_dict and res_dict[key]:
                            all_entities[key].extend(res_dict[key])
                            
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
