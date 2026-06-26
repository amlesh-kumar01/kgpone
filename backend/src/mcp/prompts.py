from fastmcp import FastMCP

def register_prompts(mcp: FastMCP):

    @mcp.prompt()
    def study_guide(course_code: str) -> str:
        """Generates a study guide prompt for a given course."""
        return f"""
        You are an academic tutor. Create a comprehensive study guide for the course {course_code}.
        First, use the 'get_course_details' tool to understand the course and its prerequisites.
        Then, use the 'get_course_topics' tool to get the main topics covered in the course.
        Finally, use the 'search_documents' tool to find specific notes or materials to summarize.
        
        Format the output as a Markdown document with:
        1. Course Overview
        2. Required Prerequisites (and a brief explanation of why they are needed)
        3. Key Topics Covered
        4. Summary of Important Materials
        """

    @mcp.prompt()
    def debug_prerequisites(course_code: str) -> str:
        """Prompt to investigate missing prerequisites for a course."""
        return f"""
        I am struggling with {course_code}. Please help me figure out what prerequisites I might be missing.
        Use 'get_course_details' to see the official prerequisites.
        Then use 'answer_course_question' with the question "What are the fundamental concepts needed to understand {course_code}?"
        Provide a list of topics I should review before continuing.
        """
