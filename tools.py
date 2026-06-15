"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()
    
    # Filter by price and size first
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and size.lower() not in item["size"].lower():
            continue
        filtered.append(item)
    
    # Score each listing by keyword overlap with description
    keywords = description.lower().split()
    scored = []
    for item in filtered:
        score = 0
        searchable = " ".join([
            item["title"],
            item["description"],
            " ".join(item["style_tags"]),
        ]).lower()
        for keyword in keywords:
            if keyword in searchable:
                score += 1
        if score > 0:
            scored.append((score, item))
    
    # Sort by score highest first
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()
    
    # Check if wardrobe is empty
    if not wardrobe["items"]:
        prompt = f"""You are a fashion stylist specializing in thrifted and vintage clothing.
A user is considering buying this thrifted item:
- Name: {new_item['title']}
- Description: {new_item['description']}
- Style tags: {', '.join(new_item['style_tags'])}
- Colors: {', '.join(new_item['colors'])}

They haven't entered their wardrobe yet. Give them general styling advice for this item.
What kinds of pieces pair well with it? What vibe does it suit? Keep it to 2-3 sentences."""
    else:
        wardrobe_text = "\n".join([
            f"- {item['name']} ({', '.join(item['colors'])})"
            for item in wardrobe["items"]
        ])
        prompt = f"""You are a fashion stylist specializing in thrifted and vintage clothing.
A user is considering buying this thrifted item:
- Name: {new_item['title']}
- Description: {new_item['description']}
- Style tags: {', '.join(new_item['style_tags'])}
- Colors: {', '.join(new_item['colors'])}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe.
Be specific about which wardrobe pieces to use. Keep it to 2-3 sentences."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    # Guard against empty outfit
    if not outfit or not outfit.strip():
        return "Unable to generate fit card — no outfit suggestion was provided."
    
    client = _get_groq_client()
    
    prompt = f"""You are writing an Instagram caption for a thrift outfit post.
The thrifted item is:
- Name: {new_item['title']}
- Price: ${new_item['price']}
- Platform: {new_item['platform']}

The outfit suggestion is:
{outfit}

Write a 2-4 sentence caption that sounds like a real OOTD post — casual, authentic, 
and specific. Mention the item name, price, and platform naturally once each. 
Do not make it sound like a product description. Use lowercase. Can include 1-2 emojis."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return response.choices[0].message.content