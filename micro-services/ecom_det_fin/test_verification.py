#!/usr/bin/env python3
"""
Test script to verify the comprehensive business verification system.
"""

import pytest
import requests
import time
import json


@pytest.mark.skip(reason="Integration script; not a unit test with pytest fixtures")
def test_domain(domain: str, description: str):
    """Test a domain against our verification system."""
    print(f"\n{'='*60}")
    print(f"TESTING: {domain}")
    print(f"DESCRIPTION: {description}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/check-site",
            json={"url": domain},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Risk Score: {data['risk_score']:.2f}/100")
            print(f"Badge: {data['badge']}")
            print(f"Advice: {data['advice']}")
            
            print(f"\nDETAILED BREAKDOWN:")
            for layer, details in data['layers'].items():
                print(f"  {layer.upper()}:")
                print(f"    Score: {details['score']:.2f}")
                print(f"    Weight: {details['weight']:.2f}")
                print(f"    Contribution: {details['score'] * details['weight']:.2f}")
                if details.get('details'):
                    for key, value in details['details'].items():
                        print(f"      {key}: {value}")
                print()
            
            print(f"RECOMMENDATIONS:")
            for rec in data['recommendations']:
                print(f"  • {rec}")
                
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"REQUEST ERROR: {e}")
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    """Test various domains to verify the comprehensive verification system."""
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(3)
    
    test_cases = [
        ("amazon.com", "Legitimate global e-commerce giant"),
        ("flipkart.com", "Legitimate Indian e-commerce platform"),
        ("amzon.com", "Suspicious typosquatting domain"),
        ("amazom.com", "Another suspicious typosquatting domain"),
        ("buynow-deals.com", "Generic suspicious domain name"),
        ("myntra.com", "Legitimate Indian fashion e-commerce"),
        ("quick-deals-india.xyz", "Suspicious domain with .xyz TLD"),
        ("paytm.com", "Legitimate Indian payment platform"),
        ("cashbackoffers.tk", "Suspicious free TLD domain"),
    ]
    
    for domain, description in test_cases:
        test_domain(domain, description)
        time.sleep(2)  # Rate limiting


if __name__ == "__main__":
    main()