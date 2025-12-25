import os
import json
import time

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    # New Google GenAI SDK (package: google-genai)
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except Exception:  # pragma: no cover
    genai = None
    types = None


def _safe_str(value: object) -> str:
    try:
        return str(value)
    except Exception:
        return repr(value)


def _extract_model_name(model_obj: object) -> str | None:
    """Best-effort extraction of a model name from google-genai model objects."""
    for attr in ("name", "model", "id"):
        try:
            val = getattr(model_obj, attr)
            if isinstance(val, str) and val.strip():
                return val.strip()
        except Exception:
            pass
    return None


def _model_supports_generate_content(model_obj: object) -> bool:
    """Heuristic check for whether a model supports generateContent."""
    for attr in ("supported_actions", "supported_methods", "supportedGenerationMethods", "supported_generation_methods"):
        try:
            val = getattr(model_obj, attr)
            if not val:
                continue
            # Normalize iterable -> list[str]
            items = [str(x) for x in (val if isinstance(val, (list, tuple, set)) else [val])]
            joined = " ".join(items).lower()
            if "generate" in joined or "generatecontent" in joined or "generate_content" in joined:
                return True
        except Exception:
            continue
    # If we can't tell, assume true and let the API reject it.
    return True


def _list_available_models(client) -> list[object]:
    try:
        iterable = client.models.list()
        return list(iterable)
    except Exception:
        return []


def _pick_fallback_model(client, preferred: str) -> str:
    """Pick a model name that exists for this key/project.

    - Prefer env-provided `preferred` if it's available.
    - Otherwise choose a reasonable default from the available model list.
    """
    preferred = (preferred or "").strip()
    available = _list_available_models(client)
    names: list[str] = []
    for m in available:
        name = _extract_model_name(m)
        if name:
            names.append(name)

    # Normalize names to comparable forms.
    norm = {n.replace("models/", ""): n for n in names}

    if preferred:
        pref_key = preferred.replace("models/", "")
        if pref_key in norm:
            return norm[pref_key]

    # Common candidates (newer first). We'll map to actual returned names.
    for candidate in (
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ):
        if candidate in norm:
            return norm[candidate]

    # As a last resort, return the first model that appears to support generation.
    for m in available:
        if _model_supports_generate_content(m):
            name = _extract_model_name(m)
            if name:
                return name

    # Fall back to preferred even if unknown.
    return preferred or "gemini-1.5-flash"


class GeminiQuotaError(RuntimeError):
    """Raised when the Gemini API returns quota/rate-limit exhaustion."""


def check_news_truth(news_text: str) -> dict:
    """
    Takes news article text, asks Gemini 2.5 Pro with Google Search grounding
    to evaluate whether the news is true, returns a dict with:
      - verdict: e.g. "True", "False", "Uncertain"
      - explanation: model’s reasoning (with citations)
      - grounding_metadata: search queries, sources etc.
    """

    # Best-effort: load .env for local development.
    if load_dotenv is not None:
        load_dotenv(override=False)

    if genai is None or types is None:
        raise ImportError(
            "Missing optional dependency for news verification. "
            "Install `google-genai` (and remove the `google` PyPI package if installed)."
        )

    # Ensure your Gemini API key is set
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("google_api_key")
    )
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.")

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Many keys/projects have 0 quota for higher-tier models by default.
    # Allow overriding via env. Keep default to a typically lower-cost model.
    configured_model = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    model = configured_model

    # Define the grounding tool: Google Search
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # Set up configuration to include the tool
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        # you can optionally set temperature, max output tokens etc.
        temperature=0.0  # deterministic: less “creative” output
    )

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
        response = None
        last_error: Exception | None = None
        tried_model_switch = False
        last_quota_error_msg: str | None = None

        # Simple retry for transient quota/rate limiting.
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                last_error = None
                break
            except Exception as e:
                last_error = e
                msg = _safe_str(e)

                # If the configured model doesn't exist for this API version/key, pick an available model.
                if ("404" in msg or "NOT_FOUND" in msg) and ("model" in msg.lower()) and not tried_model_switch:
                    model = _pick_fallback_model(client, configured_model)
                    tried_model_switch = True
                    continue

                # Heuristic: retry on 429 / RESOURCE_EXHAUSTED.
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    last_quota_error_msg = msg
                    # Backoff a bit; avoid hammering the API.
                    time.sleep(2 + attempt * 3)
                    continue

                raise

        if last_error is not None and response is None:
            if last_quota_error_msg is not None:
                raise GeminiQuotaError(last_quota_error_msg)
            raise last_error
        
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
        
        # Try to extract grounding metadata from the response object
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_meta = candidate.grounding_metadata
                    if hasattr(grounding_meta, 'search_entry_point') and grounding_meta.search_entry_point:
                        search_entry = grounding_meta.search_entry_point
                        if hasattr(search_entry, 'rendered_content'):
                            metadata["search_queries"] = [search_entry.rendered_content]
                    if hasattr(grounding_meta, 'grounding_chunks') and grounding_meta.grounding_chunks:
                        chunks = grounding_meta.grounding_chunks
                        sources_from_grounding = []
                        for chunk in chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                sources_from_grounding.append({
                                    "title": getattr(chunk.web, 'title', ''),
                                    "uri": getattr(chunk.web, 'uri', ''),
                                })
                        if sources_from_grounding:
                            metadata["grounding_sources"] = sources_from_grounding
        except Exception as grounding_error:
            print(f"Warning: Could not extract grounding metadata: {grounding_error}")
            metadata["grounding_extraction_error"] = str(grounding_error)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_text[:500]}...")
        
        # Fallback parsing if JSON fails
        verdict = "Uncertain"
        explanation = raw_text if 'raw_text' in locals() else "No response text available"
        parsed = {"error": "Failed to parse JSON", "raw_response": raw_text if 'raw_text' in locals() else ""}
        metadata = {"error": "Could not extract grounding metadata"}
    
    except GeminiQuotaError as e:
        # Let the FastAPI layer map this to HTTP 429.
        raise
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
