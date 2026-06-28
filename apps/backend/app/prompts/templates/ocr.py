from app.prompts.registry import PromptTemplate, PromptType

PROMPT_TYPE = PromptType.OCR

PROMPT = PromptTemplate(
    name="ocr",
    version="1.0.0",
    description="Prompt for OCR text extraction. Processes handwritten or printed text from images.",
    author="Fixly Team",
    last_updated="2026-06-26",
    template="""You are an OCR processing assistant for {user_name}, a {education_type} student.

Process the following extracted text. Correct any OCR errors while preserving original meaning. Format the output clearly. Identify whether the text is handwritten notes, printed documents, screenshots of textbooks, or code. Present the cleaned text and optionally provide a brief summary.

Raw extracted text:
{content}""",
)
