from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base_generator import BaseMarkdownGenerator

class FormulaGenerator(BaseMarkdownGenerator):
    async def generate(self, ast_data: Dict[str, Any], topics: List[str], prompt: str, doc_title: str) -> str:
        context = self.filter_ast(ast_data, topics)
        
        system_prompt = f"""You are an expert academic tutor creating a formula sheet.
The user is studying a document titled '{doc_title}'.
Topics requested: {', '.join(topics) if topics else 'All'}

Your task is to extract mathematical formulas and equations related to the user's prompt.
Format the output as a beautiful Markdown document.

Include:
- A main title (e.g., `# Formula Sheet`)
- Subheadings for different concepts if applicable
- A Markdown table for the formulas, with columns: `| Formula | Variables | Notes |`
- Use proper LaTeX formatting for formulas, enclosed in `$` for inline or `$$` for block.

User Prompt: {prompt}
"""
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Document Context:\n{context}\n\nPlease generate the formula sheet.")
        ])
        
        chain = chat_prompt | self.llm
        res = await chain.ainvoke({"context": context})
        return res.content
