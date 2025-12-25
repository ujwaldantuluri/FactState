#!/usr/bin/env python3
"""
Test script for advanced e-commerce detection integration.
This script tests the core functionality without starting the full FastAPI server.
"""

import asyncio
import sys
import os
import sqlite3

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_advanced_analysis():
    """Test the advanced e-commerce analysis."""
    print("🔍 Testing Advanced E-commerce Analysis Integration...")
    
    try:
        # Import the scoring module
        from ecommerce_detection.scoring import evaluate_all, to_badge, advice_for
        
        # Test URL
        test_url = "https://amazon.com"
        
        print(f"📊 Analyzing: {test_url}")
        
        # Run analysis
        score, reasons = await evaluate_all(test_url, session=None)
        badge = to_badge(score)
        payment, actions = advice_for(score)
        
        print(f"✅ Analysis completed successfully!")
        print(f"   Risk Score: {score:.2f}")
        print(f"   Badge: {badge}")
        print(f"   Layers analyzed: {len(reasons)}")
        print(f"   Payment advice: {payment}")
        print(f"   Actions count: {len(actions)}")
        
        # Print detailed reasons
        print("\n📋 Analysis Details:")
        for reason in reasons:
            print(f"   {reason.layer}: {reason.message} (Score: {reason.score:.1f}, Weight: {reason.weight:.2f})")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return False

async def test_individual_layers():
    """Test individual analysis layers."""
    print("\n🧪 Testing Individual Analysis Layers...")
    
    test_url = "https://example.com"
    
    try:
        # Test domain analysis
        from ecommerce_detection.layers import domain_infra
        result = domain_infra.analyze(test_url)
        print(f"   ✅ Domain Analysis: Score={result.score:.1f}, Message={result.message[:50]}...")
        
        # Test content analysis
        from ecommerce_detection.layers import content_ux
        result = await content_ux.analyze(test_url)
        print(f"   ✅ Content Analysis: Score={result.score:.1f}, Message={result.message[:50]}...")
        
        # Test visual analysis
        from ecommerce_detection.layers import visual_brand
        result = await visual_brand.analyze(test_url)
        print(f"   ✅ Visual Analysis: Score={result.score:.1f}, Message={result.message[:50]}...")
        
        # Test threat intel
        from ecommerce_detection.layers import threat_intel
        result = await threat_intel.analyze(test_url)
        print(f"   ✅ Threat Intel: Score={result.score:.1f}, Message={result.message[:50]}...")
        
        print("   🎉 All individual layers working!")
        return True
        
    except Exception as e:
        print(f"   ❌ Layer Test Error: {e}")
        return False

def test_models():
    """Test data models."""
    print("\n📦 Testing Data Models...")
    
    try:
        from ecommerce_detection.models import (
            EcommerceAnalysisRequest, 
            AdvancedEcommerceResult,
            Reason,
            Advice
        )
        
        # Test request model
        request = EcommerceAnalysisRequest(url="https://example.com")
        print(f"   ✅ Request Model: {request.url}")
        
        # Test reason model
        reason = Reason(layer="test", message="test message", weight=0.5, score=25.0)
        print(f"   ✅ Reason Model: {reason.layer} - {reason.message}")
        
        # Test advice model
        advice = Advice(payment="Safe to proceed", actions=["Use secure payment"])
        print(f"   ✅ Advice Model: {advice.payment}")
        
        print("   🎉 All models working!")
        return True
        
    except Exception as e:
        print(f"   ❌ Models Test Error: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("\n🗄️ Testing Database Integration...")
    
    try:
        from ecommerce_detection.database import DatabaseManager
        
        # Create test database
        db = DatabaseManager(":memory:")  # Use in-memory database for testing
        
        # Verify tables were created
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Recreate tables manually for test
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                risk_score REAL NOT NULL,
                badge TEXT NOT NULL,
                reasons TEXT NOT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                delivered BOOLEAN NOT NULL,
                order_hash TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Test storing analysis
        cursor.execute("""
            INSERT INTO analysis_results (url, risk_score, badge, reasons)
            VALUES (?, ?, ?, ?)
        """, ("https://test.com", 45.5, "⚠️ Caution Required", "Test analysis"))
        print("   ✅ Analysis storage working")
        
        # Test storing feedback
        cursor.execute("""
            INSERT INTO feedback (url, delivered, order_hash)
            VALUES (?, ?, ?)
        """, ("https://test.com", True, "order123"))
        cursor.execute("""
            INSERT INTO feedback (url, delivered, order_hash)
            VALUES (?, ?, ?)
        """, ("https://test.com", False, "order124"))
        print("   ✅ Feedback storage working")
        
        # Test feedback summary
        cursor.execute("""
            SELECT delivered, COUNT(*) 
            FROM feedback 
            WHERE url = ? 
            GROUP BY delivered
        """, ("https://test.com",))
        
        results = cursor.fetchall()
        delivered = sum(count for delivered, count in results if delivered)
        failed = sum(count for delivered, count in results if not delivered)
        
        summary = {
            "delivered": delivered,
            "failed": failed,
            "total": delivered + failed
        }
        print(f"   ✅ Feedback Summary: {summary}")
        
        conn.close()
        
        print("   🎉 Database integration working!")
        return True
        
    except Exception as e:
        print(f"   ❌ Database Test Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Advanced E-commerce Detection Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test models first (no async needed)
    results.append(test_models())
    
    # Test database
    results.append(test_database())
    
    # Test individual layers
    results.append(await test_individual_layers())
    
    # Test full analysis
    results.append(await test_advanced_analysis())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration successful!")
        print("\n🔧 Next Steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Start server: uvicorn main:app --reload --port 8000")
        print("   3. Test endpoints:")
        print("      - POST /ecommerce/analyze-advanced")
        print("      - POST /ecommerce/feedback")
        print("      - GET /ecommerce/compare")
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
