import logging
import uuid
from sqlalchemy.orm import Session
from src.infrastructure.database import SessionLocal
from src.repositories.postgres.chat_repository import ChatRepository
from src.infrastructure.llm_factory import LLMFactory
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger("memory_tasks")

async def extract_user_memory_task(conversation_id: uuid.UUID):
    """
    Background task to analyze a conversation and extract persistent facts about the user.
    """
    try:
        with SessionLocal() as session:
            repo = ChatRepository(session)
            conversation = repo.get_conversation(conversation_id, load_messages=True)
            if not conversation or len(conversation.messages) < 3:
                return # Not enough data
                
            # Combine messages into a transcript
            transcript = ""
            for msg in conversation.messages:
                if msg.role.value in ["user", "assistant"]:
                    transcript += f"{msg.role.value.capitalize()}: {msg.content}\n\n"
                    
            llm_factory = LLMFactory()
            try:
                llm = llm_factory.get_llm()
            except Exception:
                logger.warning("Could not get LLM for memory extraction")
                return
                
            prompt = PromptTemplate.from_template(
                """Analyze the following conversation transcript between a student and an AI tutor.
You have three tasks:
1. Extract permanent facts about the student (e.g. "prefers visual explanations", "struggles with algebra").
2. Write a concise 1-2 sentence summary of the entire conversation so far.
3. Extract 3-5 important keywords/topics discussed.

Output your response STRICTLY as a JSON object matching this schema:
{{
  "facts": ["fact 1", "fact 2"],
  "summary": "The student asked about...",
  "keywords": ["topic1", "topic2"]
}}

Transcript:
{transcript}"""
            )
            
            chain = prompt | llm
            response = await chain.ainvoke({"transcript": transcript})
            content = response.content.strip()
            
            import json
            import re
            
            try:
                # Strip markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                    
                data = json.loads(content.strip())
                
                # 1. Update Memories
                facts = data.get("facts", [])
                for fact in facts:
                    if fact:
                        repo.add_user_memory(user_id=conversation.user_id, fact=fact)
                        logger.info(f"Extracted new user memory for {conversation.user_id}: {fact}")
                        
                # 2. Update Conversation Summary & Keywords
                summary = data.get("summary", "")
                keywords = data.get("keywords", [])
                keywords_str = json.dumps(keywords) if keywords else ""
                
                repo.update_conversation_summary(conversation_id, summary, keywords_str)
                logger.info(f"Updated summary for conversation {conversation_id}")
                
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse memory JSON: {je}. Raw: {content}")
                    
    except Exception as e:
        logger.error(f"Failed to extract memory for conversation {conversation_id}: {e}")
