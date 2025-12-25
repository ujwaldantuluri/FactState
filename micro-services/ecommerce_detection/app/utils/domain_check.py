import whois
from datetime import datetime

def check_domain_age(domain):
    try:
        domain_info = whois.whois(domain)

        # Get creation date safely
        creation_date = domain_info.creation_date

        # Handle case where it's a list (some WHOIS services return multiple dates)
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
            return {
                "error": "Creation date not found",
                "domain": domain,
                "is_suspicious": True
            }

        # Calculate age
        age_days = (datetime.now() - creation_date).days
        is_suspicious = age_days < 180  # e.g., less than 6 months

        return {
            "domain": domain,
            "creation_date": creation_date.strftime("%Y-%m-%d"),
            "age_days": age_days,
            "is_suspicious": is_suspicious
        }

    except Exception as e:
        return {
            "error": str(e),
            "domain": domain,
            "is_suspicious": True
        }
