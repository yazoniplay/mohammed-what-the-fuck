import json
import os
import asyncio
import traceback

from google import genai
from google.genai import types


MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_client = None


def client():
    global _client

    if _client is None:
        key = os.getenv("GEMINI_API_KEY")

        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY saknas i environment variables"
            )

        _client = genai.Client(
            api_key=key
        )

    return _client



SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "brand": {"type": "STRING"},
        "product_type": {"type": "STRING"},
        "category": {"type": "STRING"},
        "subcategory": {"type": "STRING"},
        "color": {"type": "STRING"},
        "size": {"type": "STRING"},
        "condition": {"type": "STRING"},
        "material": {"type": "STRING"},
        "description": {"type": "STRING"},
        "suggested_price_sek": {"type": "NUMBER"},
        "price_reasoning": {"type": "STRING"},
        "confidence": {"type": "NUMBER"},
        "needs_confirmation": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "visible_defects": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "authenticity_notes": {"type": "STRING"}
    },
    "required": [
        "title",
        "category",
        "condition",
        "description",
        "suggested_price_sek",
        "needs_confirmation"
    ]
}



async def gemini_request(contents, config):

    try:

        response = await asyncio.wait_for(
            client().aio.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config
            ),
            timeout=60
        )

        if not response.text:
            raise Exception(
                "Gemini returned empty response"
            )

        return response.text


    except asyncio.TimeoutError:

        raise Exception(
            "Gemini timeout after 60 seconds"
        )


    except Exception as e:

        print("GEMINI ERROR")
        traceback.print_exc()

        raise Exception(
            f"Gemini failed: {e}"
        )



async def analyze_images(images):

    print(
        f"Analyzing {len(images)} images with {MODEL}"
    )


    parts = [
        types.Part.from_bytes(
            data=data,
            mime_type=mime
        )
        for data, mime in images
    ]


    prompt = """
Du är en svensk assistent för Vinted-listningar.

Analysera bilderna och returnera ENDAST JSON enligt schemat.

Skriv på svenska.

Hitta inte på:
- varumärke
- storlek
- material
- skick

Använd "Okänt" när det inte syns.

Beskriv endast synliga detaljer.
"""


    text = await gemini_request(
        [
            prompt,
            *parts
        ],
        types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA,
            temperature=0.2
        )
    )


    return json.loads(text)



async def regenerate_description(item):

    prompt = f"""
Skriv en kort och säljande men ärlig Vinted-beskrivning.

Titel:
{item.get('title')}

Varumärke:
{item.get('brand')}

Kategori:
{item.get('category')}

Storlek:
{item.get('size')}

Färg:
{item.get('color')}

Skick:
{item.get('condition')}

Material:
{item.get('material')}

Hitta inte på information.
"""


    return await gemini_request(
        [prompt],
        types.GenerateContentConfig(
            temperature=0.4
        )
    )



async def quality_score(item):

    prompt = f"""
Bedöm denna Vinted-annons från 0 till 100.

Titel:
{item.get('title')}

Beskrivning:
{item.get('description')}

Returnera endast JSON:
{{"score":85,"improvements":[]}}
"""


    text = await gemini_request(
        [prompt],
        types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    return json.loads(text)
