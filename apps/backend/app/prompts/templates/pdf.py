from app.prompts.registry import PromptTemplate, PromptType

PROMPT_TYPE = PromptType.PDF

PROMPT = PromptTemplate(
    name="pdf",
    version="1.0.0",
    description="Prompt for PDF document analysis. Extracts and explains content from uploaded PDFs.",
    author="Fixly Team",
    last_updated="2026-06-26",
    template="""You are a document analysis assistant for {user_name}, a {education_type} student.

Analyze the following PDF content. Extract key information, summarize main points, and explain difficult concepts. Identify the document type (research paper, textbook chapter, assignment brief, etc.) and tailor your response accordingly. Connect the content to their subjects: {subjects} if relevant.

Document content:
{content}""",
)
