import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def get_gemini_client():
    api_key = (os.getenv('GEMINI_API_KEY') or '').strip()
    if not api_key:
        raise ValueError('GEMINI_API_KEY is missing. Add it to your local .env file before using the AI assistant.')
    return genai.Client(api_key=api_key)


def explain_business_requirement(question: str, business_context: str = '') -> str:
    client = get_gemini_client()
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

    system_instruction = (
        'You are a compliance explainer for small businesses. '
        'Explain clearly in plain language, never pretend to be a legal authority, '
        'and always tell the user to verify critical information with official government sources.'
    )

    prompt = f"""
    {system_instruction}

    Business context:
    {business_context or 'No business context provided.'}

    User question:
    {question}

    Keep the answer concise and easy to scan. Use these Markdown headings in order:
    ## Short answer
    ## What applies to your business
    ## Action checklist
    ## Key terms
    ## Verify with official sources

    Use short paragraphs and simple bullet lists. Bold only short, important terms so they can be highlighted separately.
    Do not invent legal requirements, deadlines, or source links. Clearly mark details that depend on location, business type, or current rules.
    Keep the answer under 300 words. Limit the short answer to two sentences, the business-specific section to three bullets,
    the action checklist to three steps, key terms to four items, and source checks to two items.
    Remind the user to confirm legal requirements with official sources.
    """.strip()

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    return getattr(response, 'text', str(response))
