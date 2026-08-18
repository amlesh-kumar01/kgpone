from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base_generator import BaseMarkdownGenerator

class QuestionBankGenerator(BaseMarkdownGenerator):
    async def generate(self, ast_data: Dict[str, Any], topics: List[str], prompt: str, doc_title: str) -> str:
        context = self.filter_ast(ast_data, topics)
        
        system_prompt = f"""You are an expert academic tutor creating a Question Bank.
The user is studying a document titled '{doc_title}'.
Topics requested: {', '.join(topics) if topics else 'All'}

Your task is to generate questions (MCQ, Short Answer, etc.) based on the user's prompt.
Format the output as a beautiful Markdown document.

Include:
- A main title (e.g., `# Question Bank`)
- Numbered questions
- For MCQs, use bullet points for options
- Include an `**Explanation / Answer**:` section below each question.

User Prompt: {prompt}
"""
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Document Context:\n{context}\n\nPlease generate the question bank.")
        ])
        
        chain = chat_prompt | self.llm
        res = await chain.ainvoke({"context": context})
        return res.content
