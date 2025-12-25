import whois

def analyze_whois(domain):
    try:
        data = whois.whois(domain)
        registrar = data.registrar or "Unknown"
        country = data.country or "Unknown"
        email = data.emails if isinstance(data.emails, str) else (data.emails[0] if data.emails else None)

        suspicious_registrar = registrar and any(r in registrar.lower() for r in [
            "privacy", "guard", "whois", "protected", "cheap", "fastdomain"
        ])

        return {
            "registrar": registrar,
            "country": country,
            "email": email,
            "suspicious": suspicious_registrar
        }

    except Exception as e:
        return {
            "registrar": None,
            "country": None,
            "email": None,
            "suspicious": True,
            "error": str(e)
        }
