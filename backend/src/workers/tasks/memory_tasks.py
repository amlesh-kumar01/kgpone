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
            if not conversation:
                return
                
            msg_count = len(conversation.messages)
            if msg_count < 3:
                return # Not enough data
                
            # OPTIMIZATION: Only run memory extraction every 3 full turns (6 messages)
            # This drastically reduces LLM token costs and background processing overhead.
            if msg_count % 6 != 0:
                return
                
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
                
            # Fetch existing memories to merge them
            existing_memories = repo.get_user_memories(conversation.user_id)
            existing_facts = [m.fact for m in existing_memories]
            existing_facts_str = "\n".join([f"- {f}" for f in existing_facts]) if existing_facts else "None"
                
            prompt = PromptTemplate.from_template(
                """Analyze the following conversation transcript between a student and an AI tutor.
You have three tasks:
1. Extract permanent facts about the student (e.g. "prefers visual explanations", "struggles with algebra").
   - You MUST merge the new facts with the existing facts provided below.
   - If a new fact contradicts an old fact, update the old fact based on the new transcript.
   - If a new fact is similar to an old fact, merge them into a single comprehensive fact.
   - Keep the most important facts. You must NOT output more than 20 facts in total.
2. Write a concise 1-2 sentence summary of the entire conversation so far.
3. Extract 3-5 important keywords/topics discussed.

Output your response STRICTLY as a JSON object matching this schema:
{{
  "facts": ["fact 1", "fact 2"],
  "summary": "The student asked about...",
  "keywords": ["topic1", "topic2"]
}}

Existing Facts:
{existing_facts}

Transcript:
{transcript}"""
            )
            
            chain = prompt | llm
            response = await chain.ainvoke({
                "transcript": transcript,
                "existing_facts": existing_facts_str
            })
            content_raw = response.content
            if isinstance(content_raw, list):
                # Handle models that return a list of blocks
                content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content_raw])
            else:
                content = str(content_raw)
            content = content.strip()
            
            import json
            import re
            
            try:
                # Strip markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                    
                data = json.loads(content.strip())
                
                # 1. Update Memories (Consolidate and Limit to 20)
                facts = data.get("facts", [])
                facts = [f.strip() for f in facts if f and f.strip()][:20]
                
                if facts:
                    # Clear old memories and replace with the consolidated list
                    repo.clear_user_memories(conversation.user_id)
                    for fact in facts:
                        repo.add_user_memory(user_id=conversation.user_id, fact=fact)
                    logger.info(f"Consolidated and saved {len(facts)} user memories for {conversation.user_id}.")
                        
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
