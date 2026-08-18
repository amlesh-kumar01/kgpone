from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base_generator import BaseMarkdownGenerator

class RevisionNotesGenerator(BaseMarkdownGenerator):
    async def generate(self, ast_data: Dict[str, Any], topics: List[str], prompt: str, doc_title: str) -> str:
        context = self.filter_ast(ast_data, topics)
        
        system_prompt = f"""You are an expert academic tutor creating Revision Notes (Flashcard style).
The user is studying a document titled '{doc_title}'.
Topics requested: {', '.join(topics) if topics else 'All'}

Your task is to generate quick revision notes based on the user's prompt.
Format the output as a beautiful Markdown document.

Include:
- A main title (e.g., `# Revision Notes`)
- Categorize by 'Must Know', 'Good to Know', and 'Deep Dive'.
- Keep descriptions extremely concise (1-2 sentences).

User Prompt: {prompt}
"""
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Document Context:\n{context}\n\nPlease generate the revision notes.")
        ])
        
        chain = chat_prompt | self.llm
        res = await chain.ainvoke({"context": context})
        return res.content
