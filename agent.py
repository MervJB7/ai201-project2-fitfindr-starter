"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    session = _new_session(query, wardrobe)

    # Step 1: Parse the query using the LLM
    from groq import Groq
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    parse_prompt = f"""Extract search parameters from this thrift shopping query.
Query: "{query}"

Respond in this exact format, nothing else:
description: <keywords describing the item>
size: <size if mentioned, or None>
max_price: <number if mentioned, or None>"""

    parse_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": parse_prompt}],
        temperature=0.0,
    )
    
    parsed_text = parse_response.choices[0].message.content
    parsed = {"description": query, "size": None, "max_price": None}
    
    for line in parsed_text.strip().split("\n"):
        if line.startswith("description:"):
            parsed["description"] = line.split(":", 1)[1].strip()
        elif line.startswith("size:"):
            val = line.split(":", 1)[1].strip()
            parsed["size"] = None if val == "None" else val
        elif line.startswith("max_price:"):
            val = line.split(":", 1)[1].strip()
            try:
                parsed["max_price"] = float(val)
            except:
                parsed["max_price"] = None
    
    session["parsed"] = parsed

    # Step 2: Search listings
    results = search_listings(
        parsed["description"],
        parsed["size"],
        parsed["max_price"],
    )
    session["search_results"] = results

    if not results:
        session["error"] = (
            "No listings found for your search. "
            "Try different keywords, a larger size, or a higher price."
        )
        return session

    # Step 3: Select top result
    session["selected_item"] = results[0]

    # Step 4: Suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"],
        session["wardrobe"],
    )

    # Step 5: Create fit card
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )

    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
