# 🧾 Invoice Processing Service

Modern AI-powered invoice extraction using ExtractThinker with multi-model support.

## 🚀 Quick Start (Local Development)

### 1. Configure API Keys

Edit the `.env` file and add your API keys:

```bash
# Add your OpenAI API key (required for GPT models)
OPENAI_API_KEY=sk-proj-...

# Optional: Add Anthropic API key for Claude models
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Add Cohere API key
COHERE_API_KEY=...
```

### 2. Run the Service

```bash
# Activate virtual environment
source venv/bin/activate

# Start the API server
./venv/bin/python invoice_service.py

or 

./run.sh

# Or use uvicorn directly
./venv/bin/uvicorn invoice_service:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📋 Supported Models (October 2025)

### OpenAI 🚀 **NEWEST MODELS** (from official pricing)
- `gpt-5` - Flagship GPT-5 ($1.25/1M input, $10/1M output) ⭐⭐⭐
- `gpt-5-mini` - **HIGHLIGHTED** in pricing ($0.25/$2.00) 🔥 **RECOMMENDED**
- `gpt-5-nano` - Ultra-cheap ($0.05/$0.40)
- `gpt-4.1` - GPT-4.1 flagship ($2.00/$8.00)
- `gpt-4.1-mini` - GPT-4.1 mini ($0.40/$1.60)
- `gpt-4o` - GPT-4o ($2.50/$10.00)
- `gpt-4o-mini` - GPT-4o mini ($0.15/$0.60) ✅ **CHEAPEST**
- `o3` - Reasoning model ($2.00/$8.00)
- `o3-mini` - Reasoning mini ($1.10/$4.40)
- `o4-mini` - o4 series mini ($1.10/$4.40)

### Anthropic (Claude) 🚀 **NEWEST MODELS**
- `claude-sonnet-4-5-20250929` - Claude Sonnet 4.5 ⭐⭐⭐ **NEWEST FLAGSHIP**
- `claude-haiku-4-5` - Lightning-fast Claude Haiku 4.5 ⚡ **FASTEST**
- `claude-opus-4-1` - Most powerful Claude model 💪
- `claude-sonnet-4` - Claude Sonnet 4 (previous generation)
- `claude-opus-4` - Claude Opus 4 (previous generation)
- **Context**: 200K tokens standard, 1M tokens available
- **Features**: Extended thinking, vision, superior reasoning

### Ollama (Local/Free)
- `llama3.3` - Meta's latest Llama 3.3 (December 2024) ⭐
- `qwen2.5:14b` - Alibaba's Qwen 2.5, excellent multilingual
- `mistral` - Fast local inference
- `deepseek-r1:7b` - Reasoning-focused local model

### Cohere
- `command-r-plus` - Latest, best for multilingual ⭐
- `command-r` - Balanced performance
- `command` - Production-ready

## 🧪 Testing

### Test with Sample Invoice

```bash
# Test single invoice extraction
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_invoice.pdf" \
  -F "options={\"use_classification\":true,\"extract_tables\":true}"
```

### Using Python Test Script

```bash
# Make sure you have a test invoice file
./venv/bin/python test_extraction.py
```

### Using the Web UI

Navigate to http://localhost:8000/docs and use the interactive API documentation.

## 📊 API Endpoints

### 🔍 Extraction Endpoints

#### POST `/extract` - Fast Extraction (Extract Thinker)
Extract data from a single invoice using Extract Thinker (fast, accurate).

**Request:**
```bash
curl -s -X POST "http://localhost:8000/extract" \
  -F "file=@invoice/469-F01113.pdf" | jq
```

**Response:**
```json
{
  "status": "success",
  "document_type": "invoice",
  "extracted_data": {
    "invoice_number": "INV-001",
    "vendor_name": "ACME Corp",
    "total_amount": 1500.00,
    "currency": "USD",
    "invoice_date": "2025-01-15",
    "line_items": [...]
  },
  "model_used": "gpt-4o-mini",
  "processing_time": 2.34,
  "confidence_score": 0.95
}
```

**Features:**
- ⚡ Fast extraction (~5-7 seconds)
- 🎯 High accuracy with Extract Thinker
- 📋 Auto-classification of document type
- 💰 Cost-effective

---

#### POST `/extract_and_analyze` - Full Analysis (CrewAI Multi-Agent)
Deep analysis with AI validation, fraud detection, and comprehensive reporting.

**Request:**
```bash
curl -s -X POST "http://localhost:8000/extract_and_analyze" \
  -F "file=@invoice/469-F01113.pdf" | jq
```

**Response:**
```json
{
  "status": "success",
  "extracted_data": {...},
  "validation_report": {
    "is_valid": true,
    "issues_found": [],
    "recommendations": [...]
  },
  "analysis_report": {
    "risk_level": "low",
    "anomalies": [],
    "fraud_indicators": []
  },
  "comprehensive_report": "Full markdown report...",
  "processing_time": 45.67
}
```

**Features:**
- 🤖 Multi-agent AI system (CrewAI)
- ✅ Data validation agent
- 🔍 Fraud detection agent
- 📊 Comprehensive reporting agent
- ⏱️ Slower (~45-55 seconds)
- 💎 Deep insights and analysis

**Use Cases:**
- High-value invoices requiring validation
- Fraud detection and risk assessment
- Audit trail and compliance
- Detailed reporting requirements

---

#### POST `/batch_analyze` - Batch Processing with Database Storage
Process multiple invoices with automatic database storage and optional full analysis.

**Fast Mode (Default):**
```bash
curl -X POST "http://localhost:8000/batch_analyze" \
  -F "files=@invoice/invoice1.pdf" \
  -F "files=@invoice/invoice2.pdf" | jq
```

**Full Analysis Mode:**
```bash
curl -X POST "http://localhost:8000/batch_analyze?full_analysis=true" \
  -F "files=@invoice/invoice1.pdf" \
  -F "files=@invoice/invoice2.pdf" | jq
```

**Response:**
```json
{
  "status": "success",
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "filename": "invoice1.pdf",
      "status": "success",
      "invoice_id": "uuid-123",
      "extracted_data": {...},
      "analysis": {...},  // Only if full_analysis=true
      "processing_time": 6.5
    }
  ],
  "total_processing_time": 13.2
}
```

**Features:**
- 📦 Batch processing multiple files
- 💾 Automatic database storage
- 🔄 Duplicate detection (won't create duplicates)
- ⚡ Fast mode: ~5-7 sec/invoice
- 🤖 Full analysis mode: ~45-55 sec/invoice
- 📊 Aggregate statistics

**Parameters:**
- `full_analysis` (bool): Enable CrewAI multi-agent analysis
  - `false` (default): Fast extraction only
  - `true`: Full validation and risk analysis

---

#### POST `/classify` - Document Classification
Classify document type without full extraction.

**Request:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -F "file=@document.pdf" | jq
```

**Response:**
```json
{
  "document_type": "invoice",
  "confidence": 0.98,
  "processing_time": 1.2
}
```

---

### 📊 Analytics Endpoints

#### GET `/analytics/stats` - Overall Statistics
Get overall database statistics.

**Request:**
```bash
curl -s "http://localhost:8000/analytics/stats" | jq
```

**Response:**
```json
{
  "total_invoices": 7,
  "unique_vendors": 7,
  "total_amount": 2720.27,
  "average_amount": 388.61,
  "risk_distribution": {
    "high": 0,
    "medium": 2,
    "low": 5
  }
}
```

---

#### GET `/analytics/vendor/{vendor_name}` - Vendor Invoices
Get all invoices from a specific vendor with optional date filtering.

**Request:**
```bash
curl -s "http://localhost:8000/analytics/vendor/Nedstone?start_date=2025-10-01&end_date=2025-10-31" | jq
```

**Response:**
```json
{
  "vendor_name": "Nedstone",
  "invoice_count": 3,
  "total_amount": 1250.50,
  "invoices": [
    {
      "invoice_id": "uuid-123",
      "invoice_number": "INV-001",
      "invoice_date": "2025-10-15",
      "total_amount": 450.00,
      "currency": "EUR",
      "risk_level": "low"
    }
  ]
}
```

**Query Parameters:**
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)

---

#### GET `/analytics/vendor/{vendor_name}/aggregate` - Vendor Aggregates
Get aggregate statistics for a vendor by year and currency.

**Request:**
```bash
curl "http://localhost:8000/analytics/vendor/Nedstone/aggregate?year=2025" | jq
```

**Response:**
```json
{
  "vendor_name": "Nedstone",
  "year": 2025,
  "aggregates": [
    {
      "currency": "EUR",
      "invoice_count": 1,
      "total_sum": 452.44,
      "average_amount": 452.44,
      "min_amount": 452.44,
      "max_amount": 452.44,
      "first_invoice": "2025-08-01",
      "last_invoice": "2025-08-01"
    }
  ]
}
```

**Query Parameters:**
- `year` (optional): Filter by year (default: current year)

---

#### GET `/analytics/high-risk` - High Risk Invoices
Get invoices with high or medium risk levels.

**Request:**
```bash
curl -s "http://localhost:8000/analytics/high-risk?limit=10" | jq
```

**Response:**
```json
{
  "high_risk_count": 2,
  "invoices": [
    {
      "invoice_id": "uuid-456",
      "vendor_name": "Suspicious Corp",
      "total_amount": 5000.00,
      "risk_level": "high",
      "risk_factors": ["unusual_amount", "new_vendor"]
    }
  ]
}
```

---

#### POST `/analytics/chat` - Natural Language Analytics
Ask questions about invoices in natural language (Ukrainian/English).

**Request:**
```bash
curl -X POST "http://localhost:8000/analytics/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total amount of invoices from Nedstone for October 2025?"}' | jq
```

**Response:**
```json
{
  "question": "What is the total amount of invoices from Nedstone for October 2025?",
  "answer": "The total amount of invoices from Nedstone for October 2025 is 452.44 EUR",
  "sql_query": "SELECT SUM(total_amount) FROM invoices WHERE vendor_name='Nedstone' AND EXTRACT(MONTH FROM invoice_date) = 10 AND EXTRACT(YEAR FROM invoice_date) = 2025",
  "results": [{"sum": 452.44}],
  "row_count": 1,
  "timestamp": "2025-11-19T12:30:00"
}
```

**Example Questions:**
- "What is the total amount of invoices from Nedstone for October 2025?"
- "How many invoices are there from Atlassian?"
- "Top 5 vendors by total amount"
- "Which invoices have high risk?"
- "Average invoice amount from Nedstone"

**Features:**
- 🗣️ Natural language processing (Ukrainian/English)
- 🤖 AI-powered SQL query generation
- 📊 Automatic query execution
- 💬 Natural language answers

---

### 🔧 Utility Endpoints

#### GET `/health` - Health Check
Check service health and available models.

**Request:**
```bash
curl -s "http://localhost:8000/health" | jq
```

**Response:**
```json
{
  "status": "healthy",
  "service": "invoice-extractor",
  "models_available": [
    "gpt-4.1-nano",
    "gpt-5-mini",
    "gpt-5",
    "claude-sonnet-4-5-20250929",
    "gpt-4.1",
    "claude-haiku-4-5",
    "gpt-4o-mini",
    "o3-mini",
    "ollama/llama3.3"
  ]
}
```

---

#### GET `/` - API Information
Get API information and available endpoints.

**Request:**
```bash
curl -s "http://localhost:8000/" | jq
```

**Response:**
```json
{
  "service": "Invoice Processing API",
  "version": "1.0.0",
  "endpoints": [
    "/extract - Extract data from single invoice",
    "/batch_extract - Process multiple invoices",
    "/classify - Classify document type",
    "/health - Service health check"
  ],
  "supported_formats": [
    "PDF",
    "PNG",
    "JPG",
    "JPEG"
  ],
  "available_models": {
    "primary": "gpt-4.1-nano",
    "backups": [
      "gpt-5-mini",
      "gpt-5",
      "claude-sonnet-4-5-20250929",
      "gpt-4.1",
      "claude-haiku-4-5",
      "gpt-4o-mini",
      "o3-mini",
      "ollama/llama3.3"
    ]
  }
}
```

## 🏗️ Architecture

```
invoice_service.py       # Main FastAPI application
├── ExtractorManager     # Multi-model LLM management
├── InvoiceContract      # Pydantic data contract for standard invoices
├── CreditNoteContract   # Contract for credit notes
├── ReceiptContract      # Contract for simple receipts
└── API Endpoints        # REST API with async support
```

## 🔧 Configuration

All configuration is done via `.env` file:

```bash
# Model Selection (October 2025 Latest - from official pricing)
DEFAULT_MODEL=gpt-5-mini  # Highlighted in OpenAI pricing, best balance
# Alternatives: gpt-5 (flagship), gpt-4o-mini (cheapest), claude-sonnet-4-5-20250929

# API Settings
API_PORT=8000

# Processing Limits
MAX_FILE_SIZE_MB=10
PROCESSING_TIMEOUT_SECONDS=60
```

## 📈 Model Selection Logic

The system automatically selects the optimal model based on:
- **Privacy Critical**: Uses Ollama llama3.3 (local, free)
- **Reasoning Required**: Uses o3 (OpenAI reasoning)
- **Coding Required**: Uses gpt-5 (flagship)
- **Highest Accuracy**: Uses gpt-5 (flagship)
- **Budget Option**: Uses gpt-5-nano or gpt-4o-mini
- **Long Documents**: Uses Claude Sonnet 4.5 (200K-1M context)
- **Speed Critical**: Uses Claude Haiku 4.5 (lightning-fast)
- **Cost Sensitive**: Uses gpt-4o-mini (best value)
- **Multilingual**: Uses Cohere command-r-plus
- **Default**: Claude Sonnet 4.5 (newest flagship)

## 🐛 Troubleshooting

### ModuleNotFoundError
```bash
# Ensure virtual environment is activated
source venv/bin/activate
./venv/bin/pip install -r requirements.txt
```

### API Key Errors
- Check `.env` file has valid API keys
- Ensure no spaces around `=` in `.env`
- Test API key with simple OpenAI/Anthropic request

### Ollama Connection Failed
```bash
# Install and start Ollama locally
curl https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3
```

## 📝 Next Steps

1. ✅ Install dependencies
2. ✅ Configure API keys in `.env`
3. ⏳ Test with sample invoice
4. ⏳ Deploy to production (docker-compose in parent directory)
5. ⏳ Set up monitoring and alerting

## 🔗 Related Documentation

- [ExtractThinker Docs](https://github.com/enoch3712/ExtractThinker)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
