#!/usr/bin/env python3
"""
Test script for merchant verification on multi-vendor platforms
"""

import requests
import time
import json


def test_merchant_verification():
    """Test merchant verification for different platform types"""
    
    test_cases = [
        {
            "url": "https://example.myshopify.com",
            "description": "Shopify Store - Should check merchant verification",
            "expected": "Merchant verification analysis"
        },
        {
            "url": "https://etsy.com/shop/teststore",
            "description": "Etsy Shop - Should verify seller reputation", 
            "expected": "Etsy seller verification"
        },
        {
            "url": "https://ebay.com/usr/testseller",
            "description": "eBay Seller - Should check seller ratings",
            "expected": "eBay merchant analysis"
        },
        {
            "url": "https://amazon.com",
            "description": "Amazon Direct - Major platform, no merchant check needed",
            "expected": "Verified major platform"
        },
        {
            "url": "https://suspicious-store.myshopify.com",
            "description": "Suspicious Shopify Store - Should flag merchant issues",
            "expected": "Merchant verification concerns"
        }
    ]
    
    print("🛍️ MERCHANT VERIFICATION TESTING")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   URL: {test['url']}")
        print(f"   Expected: {test['expected']}")
        
        try:
            response = requests.post(
                "http://localhost:8000/scan",
                json={"url": test['url']},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"   ✅ Risk Score: {data['risk_score']:.1f}")
                print(f"   🏷️ Badge: {data['badge']}")
                
                # Look for merchant verification layer
                merchant_layer = data['layers'].get('merchant_verification', {})
                if merchant_layer:
                    print(f"   🏪 Merchant: {merchant_layer.get('message', 'No info')}")
                    print(f"   📊 Merchant Score: {merchant_layer.get('score', 'N/A')}")
                else:
                    print(f"   ⚠️ No merchant verification layer found")
                    
            else:
                print(f"   ❌ ERROR: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("🎯 MERCHANT VERIFICATION FEATURES:")
    print("   • Platform Detection (Shopify, Etsy, eBay, etc.)")
    print("   • Merchant ID/Name Extraction")
    print("   • Trust Badge Detection") 
    print("   • Seller Reputation Analysis")
    print("   • Marketplace-Specific Verification")
    print("   • Risk Scoring Based on Merchant Trust")


if __name__ == "__main__":
    test_merchant_verification()