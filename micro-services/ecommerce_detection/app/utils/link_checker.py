import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def check_broken_links(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        broken = 0
        total = 0

        for tag in links:
            href = urljoin(url, tag['href'])
            total += 1
            try:
                res = requests.head(href, timeout=3)
                if res.status_code >= 400:
                    broken += 1
            except:
                broken += 1

        suspicious = broken > 5 and (broken / total) > 0.2
        return {
            "total_links": total,
            "broken_links": broken,
            "suspicious": suspicious
        }

    except Exception as e:
        return {
            "error": str(e),
            "suspicious": False
        }
    