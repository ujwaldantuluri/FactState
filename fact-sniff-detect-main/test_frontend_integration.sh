#!/bin/bash

# Frontend Integration Test Script
echo "🧪 Testing Frontend Integration for Advanced E-commerce Detection"
echo "================================================================="

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend is not running. Please start it with:"
    echo "   cd /path/to/micro-services && uvicorn main:app --reload --port 8000"
    exit 1
fi

# Test advanced analysis endpoint
echo ""
echo "2. Testing advanced analysis endpoint..."
response=$(curl -s -X POST "http://localhost:8000/ecommerce/analyze-advanced" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.com"}')

if echo "$response" | grep -q "risk_score"; then
    echo "✅ Advanced analysis endpoint working"
    risk_score=$(echo "$response" | grep -o '"risk_score":[0-9.]*' | cut -d':' -f2)
    badge=$(echo "$response" | grep -o '"badge":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    echo "   Risk Score: $risk_score"
    echo "   Badge: $badge"
else
    echo "❌ Advanced analysis endpoint failed"
    echo "Response: $response"
fi

# Test comparison endpoint
echo ""
echo "3. Testing comparison endpoint..."
comparison_response=$(curl -s "http://localhost:8000/ecommerce/compare?url=https://amazon.com")

if echo "$comparison_response" | grep -q "basic"; then
    echo "✅ Comparison endpoint working"
else
    echo "❌ Comparison endpoint failed"
fi

# Test feedback endpoint
echo ""
echo "4. Testing feedback endpoint..."
feedback_response=$(curl -s -X POST "http://localhost:8000/ecommerce/feedback" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.com", "delivered": true, "order_hash": "test_order"}')

if [ "$?" -eq 0 ]; then
    echo "✅ Feedback endpoint working"
else
    echo "❌ Feedback endpoint failed"
fi

# Check if frontend files exist
echo ""
echo "5. Checking frontend integration files..."

files=(
    "src/pages/FakeEcommerceDetector.tsx"
    "src/lib/api.ts"
    "FRONTEND_INTEGRATION.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "🎉 Integration Test Complete!"
echo ""
echo "To start the frontend:"
echo "1. npm install (if not already done)"
echo "2. npm run dev"
echo "3. Navigate to http://localhost:5173/dashboard"
echo "4. Click on 'E-commerce Fraud Detection' card"
echo ""
echo "Test URLs to try:"
echo "- https://amazon.com (should be Verified Safe)"
echo "- https://fake-luxury-deals.com (should be high risk)"
echo "- just-domain.com (auto-adds https://)"
