from news.uitls.get_info import get_info
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

def summarize_with_gemini(queries, articles):
    model = genai.GenerativeModel('gemini-2.5-flash')
    # Prepare the text to summarize
    text = "\n\n".join([
        f"Title: {a.get('title', '')}\nContent: {a.get('content', '')}\nURL: {a.get('url', '')}" for a in articles
    ])
    prompt = f"""
    Act as an expert news analyst. Your task is to perform a targeted summary of the provided articles based *only* on the user's queries.

    **Follow these steps:**
    1.  **Identify Core Concepts:** First, deeply understand the specific entities, events, and questions within the queries: {queries}.
    2.  **Extract Relevant Facts:** Read through the articles and pull out *only* the sentences or direct phrases that explicitly address the core concepts identified in step 1.
    3.  **Synthesize the Summary:** Combine the extracted facts into a single, concise, and neutral paragraph. Begin the summary directly, without any introductory phrases like "The articles state that...".

    **Strict Rules:**
    - If you find absolutely no information in the articles that is directly relevant to the queries, your entire output must be exactly: "No relevant information found."
    - Do not include background details, your own analysis, or any information that is merely tangential to the queries.
    - Keep the summary as brief as possible while still being comprehensive of all the relevant facts found.

    **Articles to Analyze:**
    {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def verify_with_gemini(summary, query):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    You are a meticulous AI Fact-Checker. Your task is to verify the claims within a given news summary against your internal knowledge base, using the original query for context. You must output your findings in a structured JSON format.

    **Original Query for Context:**
    {query}

    **News Summary to Verify:**
    {summary}

    **Instructions (Follow these steps):**
    1.  **Identify Claims:** First, break down the summary into its core, verifiable claims.
    2.  **Internal Verification:** For each claim, cross-reference it with your vast internal knowledge base up to your last training cut-off. Assess if the claims are well-established facts, disputed information, or misinformation.
    3.  **Synthesize Findings:** Based on your verification, determine an overall status, confidence level, and a concise justification. The justification should explain *why* the summary is considered true, false, or partially true, referencing the specific claims.
    4.  **Construct JSON:** Populate the JSON object below with your findings.

    **Output Rules:**
    - Your entire response MUST be a single, valid JSON object and nothing else.
    - Do not include any text, notes, or explanations outside of the JSON structure.
    - Generate the current timestamp in UTC 'YYYY-MM-DDTHH:MM:SSZ' format.

    **JSON Output Structure:**
    ```json
    {{
        "status": "A string, either 'VERIFIED' if a conclusion was reached, or 'CANNOT_VERIFY' if you lack sufficient information.",
        "verification_result": "A string, one of: 'Likely True', 'Partially True', 'Likely False', or 'Unverifiable'.",
        "confidence": "An integer between 0 and 100 representing your confidence in the verification_result.",
        "timestamp": "The current UTC timestamp in ISO 8601 format (e.g., '2025-07-10T15:45:00Z').",
        "reason": "A brief, neutral, and factual justification for your assessment. Explain which claims are supported or contradicted by established facts."
    }}
    ```
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def news_main(query):
    print(f"Fetching news for: {query}")
    articles, rephrased_queries = get_info(query)
    if not articles:
        print("No articles found.")
        professional_message = "No articles were found on this topic, making the claim unverified. A lack of reporting by credible sources often indicates a claim is unsubstantiated, but does not definitively prove it is false."
        return {"summary": None, "articles": [], "verification_result": professional_message}
    print(f"Fetched {len(articles)} articles. Summarizing...")
    summary = summarize_with_gemini(rephrased_queries, articles)

    verification_result = verify_with_gemini(summary,query)

    return verification_result
