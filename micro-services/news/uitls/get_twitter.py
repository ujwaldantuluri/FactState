import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
import time

def get_twitter_post_content_2025(post_url):
    """
    Updated method for 2025 - captures background XHR requests that contain tweet data
    Uses Playwright to intercept TweetResultByRestId requests
    """
    try:
        from playwright.sync_api import sync_playwright
        import jmespath
        
        _xhr_calls = []
        
        def intercept_response(response):
            """Capture all background requests and save them"""
            if response.request.resource_type == "xhr":
                _xhr_calls.append(response)
            return response
        
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Enable background request intercepting
            page.on("response", intercept_response)
            
            # Navigate to the tweet URL
            page.goto(post_url)
            
            # Wait for tweet to load
            try:
                page.wait_for_selector("[data-testid='tweet']", timeout=10000)
            except:
                page.wait_for_timeout(5000)  # Wait a bit anyway
            
            # Find tweet background requests
            tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
            
            browser.close()
            
            if not tweet_calls:
                return {"error": "No tweet data found in background requests"}
            
            # Extract data from the first valid response
            for xhr in tweet_calls:
                try:
                    data = xhr.json()
                    tweet_result = data.get('data', {}).get('tweetResult', {}).get('result', {})
                    
                    if tweet_result:
                        # Parse the complex Twitter data structure
                        parsed_tweet = parse_tweet_data(tweet_result)
                        return parsed_tweet
                except:
                    continue
            
            return {"error": "Could not parse tweet data from background requests"}
                    
    except ImportError:
        return {"error": "Playwright not installed. Run: pip install playwright jmespath && playwright install"}
    except Exception as e:
        return {"error": f"Playwright scraping failed: {str(e)}"}

def parse_tweet_data(tweet_data):
    """Parse the complex Twitter JSON response to extract useful information"""
    try:
        import jmespath
        
        # Use jmespath to extract key fields from the complex nested structure
        parsed = jmespath.search("""
        {
            text: legacy.full_text,
            created_at: legacy.created_at,
            retweet_count: legacy.retweet_count,
            favorite_count: legacy.favorite_count,
            reply_count: legacy.reply_count,
            quote_count: legacy.quote_count,
            bookmark_count: legacy.bookmark_count,
            view_count: views.count,
            language: legacy.lang,
            tweet_id: legacy.id_str,
            conversation_id: legacy.conversation_id_str,
            hashtags: legacy.entities.hashtags[].text,
            urls: legacy.entities.urls[].expanded_url,
            user_mentions: legacy.entities.user_mentions[].screen_name,
            media: legacy.entities.media[].media_url_https,
            is_retweet: legacy.retweeted,
            is_quote: legacy.is_quote_status,
            source: source
        }
        """, tweet_data)
        
        # Extract user information
        user_data = jmespath.search("core.user_results.result", tweet_data)
        if user_data:
            user_info = jmespath.search("""
            {
                name: legacy.name,
                screen_name: legacy.screen_name,
                description: legacy.description,
                followers_count: legacy.followers_count,
                friends_count: legacy.friends_count,
                verified: legacy.verified,
                profile_image: legacy.profile_image_url_https
            }
            """, user_data)
            parsed['user'] = user_info
        
        parsed['method'] = 'playwright_xhr_2025'
        return parsed
        
    except ImportError:
        # Fallback parsing without jmespath
        result = {}
        legacy = tweet_data.get('legacy', {})
        
        result['text'] = legacy.get('full_text', '')
        result['created_at'] = legacy.get('created_at', '')
        result['retweet_count'] = legacy.get('retweet_count', 0)
        result['favorite_count'] = legacy.get('favorite_count', 0)
        result['reply_count'] = legacy.get('reply_count', 0)
        result['tweet_id'] = legacy.get('id_str', '')
        result['method'] = 'playwright_xhr_2025_fallback'
        
        # Extract user info
        user_result = tweet_data.get('core', {}).get('user_results', {}).get('result', {})
        if user_result:
            user_legacy = user_result.get('legacy', {})
            result['user'] = {
                'name': user_legacy.get('name', ''),
                'screen_name': user_legacy.get('screen_name', ''),
                'followers_count': user_legacy.get('followers_count', 0)
            }
        
        return result
    
    except Exception as e:
        return {"error": f"Failed to parse tweet data: {str(e)}"}

def get_twitter_content_twscrape(post_url):
    """
    Alternative using twscrape library - requires setup but very reliable
    """
    try:
        # This would require: pip install twscrape
        # And account setup, so returning info instead
        return {
            "error": "twscrape method requires setup",
            "info": "For production use, consider twscrape library: pip install twscrape",
            "setup_required": "Account authentication needed"
        }
    except:
        return {"error": "twscrape not available"}

def get_twitter_content_api_alternative(post_url):
    """
    Try alternative API endpoints that might still work
    """
    try:
        # Extract tweet ID
        tweet_id_match = re.search(r'/status/(\d+)', post_url)
        if not tweet_id_match:
            return {"error": "Could not extract tweet ID"}
        
        tweet_id = tweet_id_match.group(1)
        
        # Try different API endpoints
        api_urls = [
            f"https://api.twitter.com/1.1/statuses/show.json?id={tweet_id}",
            f"https://api.twitter.com/2/tweets/{tweet_id}?expansions=author_id&tweet.fields=created_at,public_metrics,text",
            f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en&token=1"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://x.com/',
        }
        
        for api_url in api_urls:
            try:
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'text' in data or 'full_text' in data:
                        return {
                            'text': data.get('text', data.get('full_text', '')),
                            'method': 'api_endpoint',
                            'api_url': api_url
                        }
            except:
                continue
        
        return {"error": "All API endpoints failed"}
        
    except Exception as e:
        return {"error": f"API method failed: {str(e)}"}

# Updated main function with the latest 2025 method
def get_twitter_post_content_robust_2025(post_url):
    """
    Most current method for 2025 - tries the latest working approaches
    """
    if not is_valid_twitter_url(post_url):
        return {"error": "Invalid X/Twitter URL"}
    
    print("Trying 2025 Playwright XHR method...")
    result = get_twitter_post_content_2025(post_url)
    if 'error' not in result and result.get('text'):
        return result
    
    print("Trying alternative API endpoints...")
    result = get_twitter_content_api_alternative(post_url)
    if 'error' not in result and result.get('text'):
        return result
    
    print("Trying Nitter instances...")
    result = get_twitter_content_via_nitter(post_url)
    if 'error' not in result:
        return result
    
    return {"error": "All 2025 methods failed", "suggestion": "Consider using official Twitter API v2 or paid scraping services"}

def is_valid_twitter_url(url):
    """Check if the URL is a valid X/Twitter post URL"""
    try:
        parsed = urlparse(url)
        return (parsed.netloc in ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'] and 
                '/status/' in parsed.path)
    except:
        return False

def extract_from_meta_tags(soup):
    """Extract content from Open Graph and Twitter meta tags"""
    content = {}
    
    # Try Open Graph tags
    og_title = soup.find('meta', property='og:title')
    og_description = soup.find('meta', property='og:description')
    
    # Try Twitter meta tags
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
    
    # Extract title
    if og_title:
        content['title'] = og_title.get('content', '').strip()
    elif twitter_title:
        content['title'] = twitter_title.get('content', '').strip()
    
    # Extract description/content
    if og_description:
        content['text'] = og_description.get('content', '').strip()
    elif twitter_description:
        content['text'] = twitter_description.get('content', '').strip()
    
    # Extract author
    twitter_creator = soup.find('meta', attrs={'name': 'twitter:creator'})
    if twitter_creator:
        content['author'] = twitter_creator.get('content', '').strip()
    
    return content if content else None

def extract_from_html_structure(soup):
    """Try to extract content from HTML structure (less reliable)"""
    content = {}
    
    # Look for tweet text in various possible selectors
    possible_selectors = [
        '[data-testid="tweetText"]',
        '.tweet-text',
        '.js-tweet-text',
        '[lang] span',
    ]
    
    for selector in possible_selectors:
        elements = soup.select(selector)
        if elements:
            text_content = ' '.join([elem.get_text().strip() for elem in elements])
            if text_content:
                content['text'] = text_content
                break
    
    return content if content else None

# More robust approaches to handle X/Twitter's anti-bot measures

def get_twitter_content_selenium(post_url):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(post_url)
        
        # Wait for tweet content to load
        wait = WebDriverWait(driver, 10)
        
        # Try multiple selectors for tweet text
        selectors = [
            '[data-testid="tweetText"]',
            '[lang] span',
            '.css-901oao.css-16my406.r-poiln3.r-bcqeeo.r-qvutc0'
        ]
        
        tweet_text = ""
        for selector in selectors:
            try:
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                tweet_text = ' '.join([elem.text for elem in elements if elem.text.strip()])
                if tweet_text:
                    break
            except:
                continue
        
        # Try to get author info
        author = ""
        try:
            author_element = driver.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
            author = author_element.text
        except:
            pass
        
        driver.quit()
        
        if tweet_text:
            return {
                'text': tweet_text,
                'author': author,
                'method': 'selenium'
            }
        else:
            return {"error": "Could not extract tweet content with Selenium"}
            
    except ImportError:
        return {"error": "Selenium not installed. Run: pip install selenium webdriver-manager"}
    except Exception as e:
        return {"error": f"Selenium extraction failed: {str(e)}"}

def get_twitter_content_via_syndication_api(post_url):
    """
    Try using Twitter's syndication API (less reliable but sometimes works)
    """
    try:
        # Extract tweet ID from URL
        import re
        tweet_id_match = re.search(r'/status/(\d+)', post_url)
        if not tweet_id_match:
            return {"error": "Could not extract tweet ID from URL"}
        
        tweet_id = tweet_id_match.group(1)
        
        # Use Twitter's syndication API
        syndication_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://twitter.com/',
        }
        
        response = requests.get(syndication_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'text': data.get('text', ''),
                'author': data.get('user', {}).get('name', ''),
                'username': data.get('user', {}).get('screen_name', ''),
                'created_at': data.get('created_at', ''),
                'method': 'syndication_api'
            }
        else:
            return {"error": f"Syndication API returned status {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Syndication API failed: {str(e)}"}

def get_twitter_content_via_nitter(post_url):
    """
    Try multiple Nitter instances
    """
    # List of Nitter instances to try
    nitter_instances = [
        'nitter.net',
        'nitter.it',
        'nitter.unixfox.eu',
        'nitter.domain.glass'
    ]
    
    for instance in nitter_instances:
        try:
            # Convert to nitter URL
            nitter_url = post_url.replace('twitter.com', instance).replace('x.com', instance)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(nitter_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try different selectors for Nitter
                tweet_content = soup.find('div', class_='tweet-content')
                if not tweet_content:
                    tweet_content = soup.find('div', class_='timeline-item')
                
                if tweet_content:
                    text = tweet_content.get_text().strip()
                    if text and "Something went wrong" not in text:
                        return {
                            'text': text,
                            'method': f'nitter_{instance}',
                            'source_instance': instance
                        }
            
        except Exception:
            continue
    
    return {"error": "All Nitter instances failed"}

# Updated main function with fallback methods
def get_twitter_post_content_robust(post_url):
    """
    Try multiple methods to extract Twitter content
    """
    if not is_valid_twitter_url(post_url):
        return {"error": "Invalid X/Twitter URL"}
    
    # Method 1: Try syndication API first (fastest)
    print("Trying syndication API...")
    result = get_twitter_content_via_syndication_api(post_url)
    if 'error' not in result:
        return result
    
    # Method 2: Try Nitter instances
    print("Trying Nitter instances...")
    result = get_twitter_content_via_nitter(post_url)
    if 'error' not in result:
        return result
    
    # Method 3: Try Selenium (most reliable but slower)
    print("Trying Selenium...")
    result = get_twitter_content_selenium(post_url)
    if 'error' not in result:
        return result
    
    # Method 4: Fall back to original method
    print("Trying original scraping method...")
    result = get_twitter_post_content(post_url)
    
    return result

def main():
    test_url = "https://x.com/unfilteredBren/status/1937329720091373575"
    result = get_twitter_post_content_robust(test_url)
    print(f"Final Result: {json.dumps(result, indent=2)}")

# Example usage with the latest 2025 methods
if __name__ == "__main__":
    # Test with your actual URL
    test_url = "https://x.com/unfilteredBren/status/1937329720091373575"
    
    print(f"Testing URL: {test_url}")
    print("=" * 50)
    
    # Try the most current method
    result = get_twitter_post_content_robust_2025(test_url)
    print(f"Final Result: {json.dumps(result, indent=2)}")