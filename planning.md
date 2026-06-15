# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the listings dataset using three filters — description keywords, size, 
and max price — and returns a list of matching items sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): keywords describing what the user is looking for, e.g. the users search term like vintage graphic tee
- `size` (str | None): the size to filter by. If None, skip size filtering entirely, show all sizes
- `max_price` (float | None): The maximum price. If None, skip price filtering entirely, show all prices

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dicts sorted by relevance (best match first). Each dict contains:
id, title, description, category, style_tags, size, condition, price, colors, brand, platform.
Returns an empty list if nothing matches.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If the list is empty, set session["error"] to "No listings found for your search. 
Try different keywords, a larger size, or a higher price." Return early without 
calling suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Takes the thrifted item found by search_listings and the user's wardrobe, then asks the LLM to suggest 1-2 complete outfit combinations using both.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the full listing dict returned by search_listings, containing
  id, title, description, category, style_tags, size, condition, price, colors, brand, platform
- `wardrobe` (dict): has one key called "items" containing a list of wardrobe item dicts.
  Each wardrobe item has: id, name, category, colors, style_tags, notes.


**What it returns:**
<!-- Describe the return value -->
A string from the LLM describing 1-2 outfit combinations using the new item 
and pieces from the wardrobe. Example: "Pair this with your baggy jeans and chunky white sneakers for a 90s streetwear look."

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If wardrobe["items"] is empty, do not crash. Instead call the LLM with a prompt 
asking for general styling advice for the item — what kinds of pieces pair well with it and what vibe it suits.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Takes the outfit suggestion string and the thrifted item, then asks the LLM to write a short casual Instagram-style caption for the complete look.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the outfit suggestion string returned by suggest_outfit
- `new_item` (dict): the full listing dict from search_listings containing
  id, title, description, category, style_tags, size, condition, price, colors, brand, platform


**What it returns:**
<!-- Describe the return value -->
A 2-4 sentence string written like a real OOTD Instagram caption. It should 
mention the item name, price, and platform naturally once each. Should sound 
casual and authentic, not like a product description.
Example: "thrifted this faded band tee off depop for $22 and it was made for 
my wide-legs full look in my stories"
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or whitespace-only, return the string:
"Unable to generate fit card — no outfit suggestion was provided."
Do not call the LLM and do not raise an exception.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

Step 1: Parse the user's query to extract three values: description (keywords),
size (if mentioned), and max_price (if mentioned). Store these in session["parsed"].

Step 2: Call search_listings() with the parsed values. Store results in 
session["search_results"]. 
- If results are empty: set session["error"] to "No listings found for your 
  search. Try different keywords, a larger size, or a higher price." Return 
  the session immediately. Do NOT call suggest_outfit or create_fit_card.
- If results are not empty: select the top result (results[0]) and store it 
  in session["selected_item"]. Proceed to Step 3.

Step 3: Call suggest_outfit() with session["selected_item"] and session["wardrobe"].
Store the returned string in session["outfit_suggestion"]. Proceed to Step 4.

Step 4: Call create_fit_card() with session["outfit_suggestion"] and 
session["selected_item"]. Store the returned string in session["fit_card"].

Step 5: Return the completed session. The agent is done when session["fit_card"] 
is set or session["error"] is set — whichever comes first.
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

All state is stored in a single session dict that is initialized at the start 
of each interaction and passed through every step. The session tracks:

- session["query"]: the original user query string
- session["parsed"]: dict containing extracted description, size, and max_price
- session["search_results"]: full list of matching listing dicts from search_listings
- session["selected_item"]: the top result from search_results, passed into suggest_outfit
- session["wardrobe"]: the user's wardrobe dict, passed into suggest_outfit
- session["outfit_suggestion"]: the string returned by suggest_outfit, passed into create_fit_card
- session["fit_card"]: the final caption string returned by create_fit_card
- session["error"]: set to an error message string if the interaction ends early, 
  otherwise None

No tool receives the session dict directly — each tool only receives the specific 
values it needs. The planning loop reads from and writes to the session between 
each tool call.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set session["error"] to "No listings found for your search. Try different keywords, a larger size, or a higher price." Return session immediately without calling suggest_outfit or create_fit_card. |
| suggest_outfit | Wardrobe is empty | Do not crash. Call the LLM with a prompt asking for general styling advice for the item instead of wardrobe-specific combinations.  |
| create_fit_card | Outfit input is missing or incomplete | Return the string "Unable to generate fit card — no outfit suggestion was provided." Do not call the LLM and do not raise an exception.  |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

     User query

│

▼

Planning Loop

│

├─► Step 1: Parse query → extract description, size, max_price

│       │

│       ▼

│   session["parsed"] = {description, size, max_price}

│       │

├─► Step 2: search_listings(description, size, max_price)

│       │

│       ├── results == [] ──► set session["error"] → RETURN EARLY

│       │

│       └── results != [] ──► session["selected_item"] = results[0]

│               │

├─► Step 3: suggest_outfit(selected_item, wardrobe)

│       │

│       ├── wardrobe empty ──► LLM gives general styling advice

│       │

│       └── wardrobe not empty ──► LLM suggests specific outfit combos

│               │

│           session["outfit_suggestion"] = result

│               │

├─► Step 4: create_fit_card(outfit_suggestion, selected_item)

│       │

│       ├── outfit empty ──► return error string

│       │

│       └── outfit not empty ──► LLM generates Instagram caption

│               │

│           session["fit_card"] = result

│               │

└─► Step 5: Return completed session

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

For search_listings: I will give Claude the Tool 1 spec from planning.md 
(inputs, return value, failure mode) and ask it to implement the function 
using load_listings() from utils/data_loader.py. I will verify the generated 
code filters by all three parameters and handles the empty results case. 
Then I will test it with 3 different queries before using it.

For suggest_outfit: I will give Claude the Tool 2 spec from planning.md and 
ask it to implement the function using the Groq client with llama-3.3-70b-versatile. 
I will verify it handles the empty wardrobe case and returns a non-empty string.
I will test it with both get_example_wardrobe() and get_empty_wardrobe().

For create_fit_card: I will give Claude the Tool 3 spec from planning.md and 
ask it to implement the function using the Groq client. I will verify it guards 
against empty outfit input and produces varied output each time. I will run it 
3 times on the same input to confirm the captions differ.

**Milestone 4 — Planning loop and state management:**

I will give Claude the full Architecture diagram and the Planning Loop and 
State Management sections from planning.md and ask it to implement run_agent() 
in agent.py. I will verify the generated code branches on search_listings results,
stores values in the session dict, and does not call all three tools unconditionally.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. 
I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the query and extracts:
- description: "vintage graphic tee"
- size: None (not mentioned)
- max_price: 30.0
Stores these in session["parsed"]. Calls search_listings("vintage graphic tee", None, 30.0).

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings returns 3 matching listings sorted by relevance:
- lst_006: Graphic Tee — 2003 Tour Bootleg Style, $24
- lst_033: Vintage Band Tee — Faded Grey, $19
- lst_015: Vintage Graphic Hoodie — Faded Black, $26
The agent selects results[0] (lst_006) and stores it in session["selected_item"].
Calls suggest_outfit(selected_item, wardrobe).

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit receives the graphic tee and the example wardrobe. The wardrobe 
is not empty so the LLM suggests specific combinations:
"Pair this boxy graphic tee with your baggy dark wash jeans and chunky white 
sneakers for a classic 90s streetwear look. Tuck the front corner slightly for 
shape and throw your black denim jacket over the top if it gets cold."
Stores this in session["outfit_suggestion"]. Calls create_fit_card(outfit_suggestion, selected_item).

**Step 4:**
<!-- What does the user actually see at the end? -->
create_fit_card receives the outfit suggestion and the graphic tee listing.
The LLM generates: "found this 2003 bootleg graphic tee on depop for $24 and 
it goes perfectly with my baggy jeans this is the thrift find of the year 
fr, full fit in my stories"
Stores this in session["fit_card"].

**Final output to user:**
- Panel 1 (listing): Graphic Tee — 2003 Tour Bootleg Style | $24 | depop | Size L | Condition: good
- Panel 2 (outfit): "Pair this boxy graphic tee with your baggy dark wash jeans..."
- Panel 3 (fit card): "found this 2003 bootleg graphic tee on depop for $24..."