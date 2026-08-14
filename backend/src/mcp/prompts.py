from fastmcp import FastMCP

def register_prompts(mcp: FastMCP):

    @mcp.prompt()
    def study_guide(study_unit_code: str) -> str:
        """Generate a comprehensive study guide for a course."""
        return f"""
You are an academic tutor. Create a comprehensive study guide for the course {study_unit_code}.

Follow these steps:
1. Call `get_prerequisites('{study_unit_code}')` to understand what background knowledge is required.
2. Call `get_course_documents('{study_unit_code}')` to see what materials are available.
3. Call `lookup_knowledge_graph('<main topic>')` to understand the concept map.
4. Call `answer_question('What are the key topics covered in {study_unit_code}?', '{study_unit_code}')` for a summary.

Format the output as a Markdown document with:
1. StudyUnit Overview
2. Required Prerequisites (and why they matter)
3. Key Topics & Concept Map
4. Summary of Important Materials
5. Suggested Study Order
"""

    @mcp.prompt()
    def debug_prerequisites(study_unit_code: str) -> str:
        """Help a student identify what prerequisites they might be missing."""
        return f"""
A student is struggling with {study_unit_code}. Help identify what prerequisites they might be missing.

Steps:
1. Call `get_prerequisites('{study_unit_code}')` to list official prerequisites.
2. Call `answer_question('What fundamental concepts are needed for {study_unit_code}?', '{study_unit_code}')` for deeper context.
3. For each prerequisite, call `get_course_documents('<prereq_code>')` to find available study materials.

Provide:
- A list of prerequisite concepts they must understand
- Specific topics to review for each prerequisite
- Recommended documents to read (with IDs so the student can download them)
"""

    @mcp.prompt()
    def exam_prep(study_unit_code: str) -> str:
        """Generate an exam preparation guide using past year questions."""
        return f"""
Help a student prepare for their {study_unit_code} exam using past year questions (PYQs).

Steps:
1. Call `get_course_documents('{study_unit_code}', 'PYQ')` to find all past year papers.
2. For each paper found, use `fetch_document_metadata('<doc_id>')` to get details.
3. Call `answer_question('What are the most commonly asked topics in {study_unit_code} exams?', '{study_unit_code}')` to identify patterns.
4. Call `answer_question('What are the most important formulas and theorems in {study_unit_code}?', '{study_unit_code}')` for key content.

Provide:
- A list of all available PYQs with download links
- Common exam topics and question patterns
- Key formulas, theorems, and concepts to memorise
- Topic-by-topic revision checklist
"""

    @mcp.prompt()
    def concept_deep_dive(topic: str, study_unit_code: str) -> str:
        """Generate a deep-dive explanation of a specific academic concept."""
        return f"""
Provide an in-depth explanation of "{topic}" in the context of {study_unit_code}.

Steps:
1. Call `answer_question('Explain {topic} in detail', '{study_unit_code}')` for the primary explanation.
2. Call `lookup_knowledge_graph('{topic}')` to find related concepts and connections.
3. Call `semantic_search('{topic} examples applications', '{study_unit_code}')` for practical examples.

Structure your response as:
1. **What is {topic}?** — Clear definition
2. **How it works** — Step-by-step explanation
3. **Mathematical formulation** (if applicable)
4. **Related Concepts** — From the knowledge graph
5. **Real-world Applications**
6. **Common Exam Questions** on this topic
"""
