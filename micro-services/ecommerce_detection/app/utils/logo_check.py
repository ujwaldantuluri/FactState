import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PIL import Image
import imagehash
from io import BytesIO
import os

# Load known brand logo hashes once
BRAND_LOGOS = {
    "Amazon": imagehash.average_hash(Image.open("/home/shasank/shasank/Hackathon/WOW-githm/fack-finder/micro-services/ecommerce_detection/app/assets/amazon_logo.png")),
    "Flipkart": imagehash.average_hash(Image.open("/home/shasank/shasank/Hackathon/WOW-githm/fack-finder/micro-services/ecommerce_detection/app/assets/flipkart_logo.png")),
    # Add more logos as needed
}

def fetch_logo_url(website_url):
    try:
        resp = requests.get(website_url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")

        # First try <link rel="icon">
        icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if icon_link and icon_link.get("href"):
            return urljoin(website_url, icon_link["href"])

        # Fallback to first <img>
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            return urljoin(website_url, img_tag["src"])

    except Exception as e:
        print(f"Logo fetch failed: {e}")
    return None

def check_logo_similarity(website_url):
    logo_url = fetch_logo_url(website_url)
    if not logo_url:
        return {
            "logo_found": False,
            "suspicious": False,
            "reason": "Logo not found or inaccessible"
        }

    try:
        img_response = requests.get(logo_url, timeout=5)
        logo_image = Image.open(BytesIO(img_response.content)).convert("RGB")
        test_hash = imagehash.average_hash(logo_image)

        for brand, known_hash in BRAND_LOGOS.items():
            diff = test_hash - known_hash
            if diff < 10:  # Threshold for suspicious similarity
                return {
                    "logo_found": True,
                    "suspicious": True,
                    "matched_brand": brand,
                    "hash_difference": diff,
                    "logo_url": logo_url
                }

        return {
            "logo_found": True,
            "suspicious": False,
            "hash_difference": "No close match found",
            "logo_url": logo_url
        }

    except Exception as e:
        return {
            "logo_found": False,
            "suspicious": False,
            "error": f"Logo processing failed: {e}"
        }
    