from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlparse

from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file


from utils.domain_check import check_domain_age
from utils.ssl_check import check_ssl_certificate
from utils.logo_check import check_logo_similarity
from utils.pattern_check import detect_suspicious_patterns
from utils.safe_browsing import check_safe_browsing
from utils.whois_check import analyze_whois
from utils.headers_check import analyze_headers
from utils.link_checker import check_broken_links

# ✅ Define Pydantic request model
class UrlRequest(BaseModel):
    url: str

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "✅ Fake E-commerce Website Detector is running!"}

@app.post("/analyze")
async def analyze(data: UrlRequest):
    url = data.url

    # ✅ Validate and extract domain
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc.replace("www.", "") if parsed_url.netloc else parsed_url.path

    # ✅ Perform all checks
    domain_info = check_domain_age(domain_name)
    ssl_info = check_ssl_certificate(domain_name)
    logo_info = check_logo_similarity(url)
    pattern_info = detect_suspicious_patterns(url)
    safe_browsing_info = check_safe_browsing(url)
    whois_info = analyze_whois(domain_name)
    headers_info = analyze_headers(url)
    link_info = check_broken_links(url)

    # ✅ Final risk score calculation
    risk_score = sum([
        int(domain_info.get('is_suspicious', False)),
        int(logo_info.get('suspicious', False)),
        int(pattern_info.get('is_suspicious', False)),
        int(not ssl_info.get('is_valid', True)),
        int(not safe_browsing_info.get('safe', True)),
        int(whois_info.get('suspicious', False)),
        int(headers_info.get('suspicious', False)),
        int(link_info.get('suspicious', False)),
    ])

    # ✅ Final verdict
    verdict = "Unsafe" if risk_score >= 5 else "Safe"

    return {
        "domain": domain_info,
        "ssl": ssl_info,
        "logo": logo_info,
        "patterns": pattern_info,
        "safe_browsing": safe_browsing_info,
        "whois": whois_info,
        "headers": headers_info,
        "links": link_info,
        "risk_score": risk_score,
        "verdict": verdict
    }