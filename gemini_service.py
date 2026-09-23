import json
import os
from google import genai
from google.genai import types

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_client = None

def client():
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY saknas")
        _client = genai.Client(api_key=key)
    return _client

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"}, "brand": {"type": "STRING"},
        "product_type": {"type": "STRING"}, "category": {"type": "STRING"},
        "subcategory": {"type": "STRING"}, "color": {"type": "STRING"},
        "size": {"type": "STRING"}, "condition": {"type": "STRING"},
        "material": {"type": "STRING"}, "description": {"type": "STRING"},
        "suggested_price_sek": {"type": "NUMBER"}, "price_reasoning": {"type": "STRING"},
        "confidence": {"type": "NUMBER"}, "needs_confirmation": {"type": "ARRAY", "items": {"type": "STRING"}},
        "visible_defects": {"type": "ARRAY", "items": {"type": "STRING"}},
        "authenticity_notes": {"type": "STRING"}
    }, "required": ["title", "category", "condition", "description", "suggested_price_sek", "needs_confirmation"]
}

async def analyze_images(images):
    parts = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in images]
    prompt = '''Du är en svensk assistent för Vinted-listningar. Analysera bilderna och returnera ENDAST JSON enligt schemat. Skriv på svenska. Hitta inte på varumärke, storlek, material eller skick. Använd "Okänt" när det inte syns. Beskriv bara synliga detaljer. Pris är en preliminär uppskattning i SEK. Markera osäkerheter i needs_confirmation och varna för att äkthet inte kan bekräftas från bilder ensam.'''
    response = await client().aio.models.generate_content(
        model=MODEL, contents=[prompt, *parts],
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SCHEMA, temperature=0.2)
    )
    return json.loads(response.text)
