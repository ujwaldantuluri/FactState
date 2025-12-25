import logging
from dotenv import load_dotenv
from .scrape_wed import WebScrapingAgent
from dataclasses import asdict
from .get_urls import NewsSearcher
import os

try:
    # Legacy Gemini SDK (package: google-generativeai)
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None

# Basic logger setup
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

# Load environment variables
load_dotenv()

# Configure the API key once when the module is loaded
# Ensure your .env file has GOOGLE_API_KEY="your_key_here"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found. Rephrase model may not work.")
else:
    if genai is None:
        logger.warning("google-generativeai is not installed. Rephrase model may not work.")
    else:
        genai.configure(api_key=GOOGLE_API_KEY)


def rephrase_query_for_search(original_query: str) -> list[str]:
    """
    Rephrases a query into three different formats for news verification.
    """
    try:
        if not GOOGLE_API_KEY:
            logger.warning("Skipping rephrase: GOOGLE_API_KEY missing.")
            return [original_query]

        if genai is None:
            logger.warning("Skipping rephrase: google-generativeai not installed.")
            return [original_query]

        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Act as an expert search strategist for an investigative news desk. Your task is to reformulate a user's query into three distinct, powerful search strings to effectively verify a news story.

        **Original Query:**
        "{original_query}"

        **Your Process:**
        1.  **Analyze:** First, identify the key people, organizations, locations, events, and specific claims in the original query.
        2.  **Generate 3 Query Variants:** Based on your analysis, create the following three types of search queries.

        **Query Types to Generate:**
        1.  **The Core Facts (Who/What/Where):** A direct, neutral keyword query focusing on the primary entities and the core action of the event.
        2.  **The Skeptical Inquiry (Verification):** A query designed to find counter-arguments, fact-checks, or debunks. It should question the claim directly using terms like "fact check," "evidence," "hoax," or "controversy."
        3.  **The Bigger Picture (Why/How):** A broader query to find the background and context that led to the event.

        **Output Requirement:**
        - Your entire response MUST consist of only the three generated queries.
        - Each query must be on a new line.
        - Do NOT include numbers, labels (like "The Core Facts:"), or any other explanatory text.
        """
        response = model.generate_content(prompt)

        # The split() and strip() logic is now more reliable due to the strict prompt.
        rephrased_queries = [q.strip() for q in (response.text or "").strip().split('\n')]
        queries = [q for q in rephrased_queries if q]
        if not queries:
            logger.warning("Rephrase produced no queries; falling back to original.")
            return [original_query]
        return queries

    except Exception as e:
        logger.error(f"An error occurred during rephrasing: {e}")
        return [original_query]

def get_info(query: str):
    """
    Rephrases a query, searches for news articles using the rephrased queries,
    scrapes the content, and returns the structured data.

    Args:
        query: The initial user query.

    Returns:
        A tuple: (list of article dicts, list of rephrased queries)
    """
    # Normalize env var names (prefer uppercase, fallback to lowercase)
    NEWS_API_KEY = os.getenv("NEWS_API_KEY") or os.getenv("news_api_key")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key")
    GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID") or os.getenv("google_search_engine_id")

    logger.info(f"Original query: {query}")
    logger.info("Rephrasing query for a wider search...")
    rephrased_queries = rephrase_query_for_search(query)
    if not rephrased_queries:
        logger.error("Could not rephrase the query. Aborting.")
        return [], []
    logger.info("Generated queries:")
    for q in rephrased_queries:
        logger.info(f"  - {q}")

    searcher = NewsSearcher(
        news_api_key=NEWS_API_KEY if NEWS_API_KEY and NEWS_API_KEY != "your_news_api_key_here" else None,
        google_api_key=GOOGLE_API_KEY if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here" else None,
        google_search_engine_id=GOOGLE_SEARCH_ENGINE_ID if GOOGLE_SEARCH_ENGINE_ID and GOOGLE_SEARCH_ENGINE_ID != "your_search_engine_id_here" else None,
    )

    available_apis = searcher.get_available_apis()
    if not available_apis:
        logger.error("No API keys configured! Set NEWS_API_KEY or both GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID.")
        return [], rephrased_queries
    else:
        logger.info(f"APIs available: {available_apis}")

    all_results = []
    seen_urls = set()
    for rephrased_query in rephrased_queries:
        logger.info(f"Searching for: '{rephrased_query}'...")
        results = searcher.search(rephrased_query, max_results=5)
        if not results:
            logger.warning("  -> No results found for this query (check API quotas, keys, or network).")
            continue
        for r in results:
            if r['url'] not in seen_urls:
                all_results.append(r)
                seen_urls.add(r['url'])

    if not all_results:
        logger.warning("No unique news results found across all rephrased queries!")
        return [], rephrased_queries

    url_data = []
    for r in all_results:
        url_data.append({
            'url': r['url'],
            'metadata': {
                'search_query': r.get('search_query', query),
                'source': r.get('source', ''),
                'api_source': r.get('api_source', ''),
                'relevance_score': 1.0
            }
        })

    logger.info(f"Scraping {len(url_data)} unique articles...")
    agent = WebScrapingAgent(delay=1.0)
    scraped_results = agent.scrape_multiple_urls(url_data)

    logger.info("Scraping complete.")
    return [asdict(res) for res in scraped_results] if scraped_results else [], rephrased_queries

def get_info_and_write_to_txt(query: str, output_file: str = "output.txt"):
    """
    Uses get_info to fetch news info for a query and writes the results to a txt file.

    Args:
        query: The search query string.
        output_file: The path to the output txt file.
    """
    results = get_info(query)
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, item in enumerate(results, 1):
            f.write(f"Result {idx}:\n")
            for key, value in item.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n" + "-"*40 + "\n\n")