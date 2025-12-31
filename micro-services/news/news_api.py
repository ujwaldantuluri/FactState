import os
import json

import google.generativeai as genai


def _is_model_not_found_error(err: Exception) -> bool:
  msg = str(err).lower()
  return (
    "is not found" in msg
    or "models/" in msg
    or "not supported" in msg
    or "listmodels" in msg
  )


def _pick_models() -> list[str]:
  # Allow override via env; otherwise prefer newer flash models first.
  # Model availability depends on your key/account/region.
  override = (os.getenv("GEMINI_MODEL") or "").strip()
  candidates = [
    override or None,
    "gemini-3.0-flash",
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
  ]
  return [m for m in candidates if m]


def check_news_truth(news_text: str) -> dict:
    """
    Takes news article text, asks Gemini 2.5 Pro with Google Search grounding
    to evaluate whether the news is true, returns a dict with:
      - verdict: e.g. "True", "False", "Uncertain"
      - explanation: model’s reasoning (with citations)
      - grounding_metadata: search queries, sources etc.
    """

    # Gemini API key: prefer GEMINI_API_KEY; fall back to GOOGLE_API_KEY for repo compatibility.
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing Gemini API key. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env")

    genai.configure(api_key=api_key)

    models_to_try = _pick_models()

    # Compose the prompt
    prompt = f"""
You are an expert fact-checker and investigative journalist. Use recent web search tools and external sources to evaluate a news article. Your goal is to decide whether the claims in the article are TRUE, FALSE, or UNCERTAIN. Provide evidence, reasoning, and your sources.

Follow these steps:

1. **Claim Extraction**
   - Read the input news article carefully.
   - Extract the key factual claims (statements that can be independently verified) — e.g. who, what, when, where, how many, etc.

2. **Identifying Keywords**
   - For each key claim, identify the main entities (people, places, organizations), dates, numbers, and other crucial details.
   - Formulate search queries using those keywords to find evidence for or against the claim.

3. **Web Search / Evidence Gathering**
   - Use web search to find multiple reputable sources (e.g. major news outlets, fact-checking sites, government / official documents).
   - Note the publication date of each source. Give preference to recent, high-credibility sources.
   - For conflicting sources, gather them all; don’t discard until you see which side is more credible.

4. **Evaluation / Context Analysis**
   - For each claim, assess whether the evidence supports, refutes, or is insufficient to decide.
   - Check if any claims are taken out of context, misquoted, or rely on ambiguous wording.
   - Assess the credibility of the sources themselves (author, date, possible bias, domain credibility).

5. **Verdict & Explanation**
   - Produce a final verdict for the whole article: **True**, **False**, or **Uncertain**.
   - For EACH key claim, say whether it is “Supported”, “Refuted”, or “Unverified / Insufficient Evidence”.
   - Provide reasoning: what evidence you found, what sources, where contradictions/uncertainty lie.

6. **Citations & Transparency**
   - List all sources you used, including URLs, titles, and dates.
   - If a claim cannot be verified, state what information is missing or what contradictory sources exist.

7. **Output Format**
   Return the result strictly as structured JSON:
   {{
     "verdict_overall": "<True | False | Uncertain>",
     "claims": [
       {{
         "claim_text": "<extracted claim>",
         "evaluation": "<Supported | Refuted | Unverified>",
         "evidence": [
            {{
              "source_title": "<title>",
              "url": "<url>",
              "publication_date": "<YYYY-MM-DD>",
              "snippet": "<short quote or paraphrase>"
            }}
         ],
         "notes": "<context/caveats>"
       }}
     ],
     "sources_used": [
       {{
         "source_title": "<title>",
         "url": "<url>",
         "publication_date": "<YYYY-MM-DD>"
       }}
     ],
     "explanation": "<narrative summary of findings>"
   }}

Article to verify:

{news_text}
"""


    # Call the Gemini API
    try:
        last_err: Exception | None = None
        response = None
        for model_name in models_to_try:
          try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            break
          except Exception as e:
            last_err = e
            if _is_model_not_found_error(e):
              continue
            raise

        if response is None:
          raise RuntimeError(
            "No usable Gemini model found. Tried: "
            + ", ".join(models_to_try)
            + (f". Last error: {last_err}" if last_err else "")
          )
        
        # Check if response is valid
        if not response or not hasattr(response, 'text'):
            raise ValueError("Invalid response from Gemini API")
            
        raw_text = response.text.strip() if response.text else ""
        
        if not raw_text:
            raise ValueError("Empty response from Gemini API")

        print(f"Raw response: {raw_text[:200]}...")  # Debug print
        
        # Parse and extract fields
        # Try to extract JSON from the response
        if raw_text.startswith('```json'):
            # Remove markdown code block formatting
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            json_text = raw_text[json_start:json_end]
        else:
            # Look for JSON object in the text
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = raw_text[json_start:json_end]
            else:
                json_text = raw_text
        
        parsed = json.loads(json_text)
        
        # Extract the main fields
        verdict = parsed.get("verdict_overall", "Uncertain")
        explanation = parsed.get("explanation", "No explanation provided")
        
        # Extract grounding metadata from the response object
        metadata = {
            "search_queries": [],
            "sources": parsed.get("sources_used", []),
            "claims_analysis": parsed.get("claims", [])
        }
        
        # Grounding metadata is only available when using SDK/tooling that supports Google Search grounding.
        # This implementation keeps metadata minimal to avoid SDK/version mismatch issues.
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_text[:500]}...")
        
        # Fallback parsing if JSON fails
        verdict = "Uncertain"
        explanation = raw_text if 'raw_text' in locals() else "No response text available"
        parsed = {"error": "Failed to parse JSON", "raw_response": raw_text if 'raw_text' in locals() else ""}
        metadata = {"error": "Could not extract grounding metadata"}
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        verdict = "Error"
        explanation = f"Error processing response: {str(e)}"
        parsed = {"error": str(e)}
        metadata = {"error": str(e)}
    
    return {
        "verdict": verdict,
        "explanation": explanation,
        "parsed_output": parsed,
        "grounding_metadata": metadata
    }
