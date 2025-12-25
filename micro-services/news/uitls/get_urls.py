import os
import logging
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')


class NewsSearcher:
    def __init__(self, news_api_key=None, google_api_key=None, google_search_engine_id=None):
        """Initialize with API keys. Add keys as you get them."""
        # Prefer uppercase envs; fallback to provided args or lowercase
        self.news_api_key = os.getenv('NEWS_API_KEY') or news_api_key or os.getenv('news_api_key')
        self.google_api_key = os.getenv('GOOGLE_API_KEY') or google_api_key or os.getenv('google_api_key')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID') or google_search_engine_id or os.getenv('google_search_engine_id')
        self.timeout = 5
        self.max_results = 20  # Increase default

        # Simple cache to avoid duplicate API calls during demo
        self._cache: Dict[str, List[Dict]] = {}

        logger.info(
            f"NewsSearcher init: NEWS_API_KEY={'SET' if self.news_api_key else 'MISSING'}, "
            f"GOOGLE_API_KEY={'SET' if self.google_api_key else 'MISSING'}, "
            f"GOOGLE_SEARCH_ENGINE_ID={'SET' if self.google_search_engine_id else 'MISSING'}"
        )

    def search_news_api(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using News API."""
        if not self.news_api_key:
            logger.warning("NewsAPI key missing; skipping NewsAPI search.")
            return []

        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': self.news_api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': min(max_results, 20)
        }

        try:
            logger.info(f"NewsAPI request -> {url} | q='{query}' pageSize={params['pageSize']}")
            response = requests.get(url, params=params, timeout=self.timeout)
            logger.info(f"NewsAPI status={response.status_code}")
            response.raise_for_status()
            data = response.json()
            if data.get('status') != 'ok':
                logger.warning(f"NewsAPI status not ok: {data}")

            results: List[Dict] = []
            for article in data.get('articles', []):
                if not article.get('title'):
                    continue
                results.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'snippet': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'api_source': 'news_api'
                })
            return results

        except requests.HTTPError as http_e:
            body = None
            try:
                body = response.text
            except Exception:
                body = None
            logger.error(f"NewsAPI HTTP error: {http_e}; body={body}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

    def search_google_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using Google Custom Search API."""
        if not self.google_api_key or not self.google_search_engine_id:
            logger.warning("Google CSE keys missing; skipping Google search.")
            return []

        all_results: List[Dict] = []
        requests_needed = (max_results + 9) // 10

        for request_num in range(requests_needed):
            start_index = request_num * 10 + 1
            current_request_limit = min(10, max_results - len(all_results))
            if current_request_limit <= 0:
                break

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_search_engine_id,
                'q': f"{query} news",
                'num': current_request_limit,
                'start': start_index,
                'sort': 'date'
            }

            try:
                logger.info(f"Google CSE request -> {url} | q='{params['q']}' num={params['num']} start={params['start']}")
                response = requests.get(url, params=params, timeout=self.timeout)
                logger.info(f"Google CSE status={response.status_code}")
                response.raise_for_status()
                data = response.json()

                items = data.get('items', [])
                if not items:
                    logger.info("Google CSE returned no items; stopping pagination.")
                    break

                for item in items:
                    source = item.get('displayLink', 'Unknown')
                    if '.' in source:
                        source = source.split('.')[0].title()
                    all_results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': source,
                        'published_at': '',
                        'api_source': 'google_search'
                    })

            except requests.HTTPError as http_e:
                body = None
                try:
                    body = response.text
                except Exception:
                    body = None
                logger.error(f"Google CSE HTTP error on request {request_num + 1}: {http_e}; body={body}")
                break
            except Exception as e:
                logger.error(f"Google CSE error on request {request_num + 1}: {e}")
                break

        return all_results

    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs."""
        seen_urls = set()
        unique_results: List[Dict] = []
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        return unique_results

    def search(self, query: str, max_results: int = None) -> List[Dict]:
        """Try multiple APIs and combine results."""
        if max_results is None:
            max_results = self.max_results

        cache_key = f"{query}_{max_results}"
        if cache_key in self._cache:
            logger.info("Using cached search results.")
            return self._cache[cache_key]

        all_results: List[Dict] = []

        news_results = self.search_news_api(query, max_results // 2)
        all_results.extend(news_results)

        remaining_needed = max_results - len(all_results)
        if remaining_needed > 0 and self.google_api_key and self.google_search_engine_id:
            google_results = self.search_google_news(query, remaining_needed)
            all_results.extend(google_results)

        unique_results = self.remove_duplicates(all_results)[:max_results]
        self._cache[cache_key] = unique_results
        logger.info(f"Combined results: {len(unique_results)} (NewsAPI={len(news_results)}, Google={len(all_results) - len(news_results)})")
        return unique_results

    def get_available_apis(self) -> List[str]:
        """Check which APIs are configured."""
        apis = []
        if self.news_api_key:
            apis.append("News API")
        if self.google_api_key and self.google_search_engine_id:
            apis.append("Google Custom Search")
        return apis
    
