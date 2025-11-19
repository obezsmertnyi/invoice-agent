#!/bin/bash

# Test Invoice Extraction Script
# This script tests the invoice extraction API with a sample text invoice

echo "🧪 Testing Invoice Extraction Service..."
echo ""

# Check if service is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Service is not running on http://localhost:8000"
    echo "   Please start it with: ./run.sh"
    exit 1
fi

echo "✅ Service is running"
echo ""

# Check for API key
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  WARNING: No OpenAI API key found in .env"
    echo "   Add your key: OPENAI_API_KEY=sk-proj-..."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📤 Sending test invoice for extraction..."
echo ""

# Test with text file (simulating an image/PDF invoice)
# Note: For real PDFs, you'd use: -F "file=@invoice.pdf"
response=$(curl -s -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_invoice.txt;type=text/plain" \
  -F 'options={"use_classification":true,"extract_tables":true}')

echo "📊 Response:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Parse and show key fields
if command -v jq &> /dev/null; then
    echo "📝 Key Extracted Fields:"
    echo "  Invoice Number: $(echo "$response" | jq -r '.extracted_data.invoice_number // "N/A"')"
    echo "  Vendor: $(echo "$response" | jq -r '.extracted_data.vendor_name // "N/A"')"
    echo "  Total Amount: $(echo "$response" | jq -r '.extracted_data.total_amount // "N/A"')"
    echo "  Currency: $(echo "$response" | jq -r '.extracted_data.currency // "N/A"')"
    echo "  Model Used: $(echo "$response" | jq -r '.model_used // "N/A"')"
    echo "  Processing Time: $(echo "$response" | jq -r '.processing_time // "N/A"')s"
else
    echo "💡 Install 'jq' for better JSON parsing: sudo apt install jq"
fi

echo ""
echo "✅ Test completed!"
echo ""
echo "📚 Next steps:"
echo "  1. Try with a real PDF invoice: curl -X POST http://localhost:8000/extract -F 'file=@your_invoice.pdf'"
echo "  2. Open Swagger UI: http://localhost:8000/docs"
echo "  3. Check test_extraction.py for more examples"
