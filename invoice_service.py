import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import tempfile
from pathlib import Path

# ExtractThinker imports
from extract_thinker import (
    Extractor, 
    DocumentLoaderPyPdf,
    Contract,
    Classification,
    Process,
    SplittingStrategy
)

# Local imports
from config import get_primary_model
from database import db
from analytics_agent import process_analytics_question

# Завантажуємо змінні оточення
load_dotenv()

# Configure litellm to drop unsupported params (e.g., temperature=0 for GPT-5)
import litellm
litellm.drop_params = True

app = FastAPI(
    title="Invoice Processing API",
    description="Automated invoice extraction using ExtractThinker",
    version="1.0.0"
)

# =================== Contracts Definition ===================

class InvoiceContract(Contract):
    """Standard Invoice Data Contract"""
    # Basic Information
    invoice_number: str = Field(description="Invoice number or ID")
    invoice_date: str = Field(description="Invoice issue date")
    due_date: Optional[str] = Field(description="Payment due date")
    
    # Vendor Information
    vendor_name: str = Field(description="Vendor/Supplier company name")
    vendor_address: Optional[str] = Field(description="Vendor address")
    vendor_tax_id: Optional[str] = Field(description="Vendor TAX ID or VAT number")
    vendor_email: Optional[str] = Field(description="Vendor contact email")
    vendor_phone: Optional[str] = Field(description="Vendor phone number")
    
    # Customer Information
    customer_name: Optional[str] = Field(description="Customer/Buyer name")
    customer_address: Optional[str] = Field(description="Customer address")
    customer_tax_id: Optional[str] = Field(description="Customer TAX ID")
    
    # Financial Information
    subtotal: float = Field(description="Subtotal amount before tax")
    tax_rate: Optional[float] = Field(description="Tax/VAT rate in percentage")
    tax_amount: Optional[float] = Field(description="Tax/VAT amount")
    discount_amount: Optional[float] = Field(default=0, description="Discount amount if any")
    total_amount: float = Field(description="Total amount including tax")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, GBP, etc.)")
    
    # Payment Information
    payment_terms: Optional[str] = Field(description="Payment terms (Net 30, etc.)")
    payment_method: Optional[str] = Field(description="Accepted payment methods")
    bank_account: Optional[str] = Field(description="Bank account details")
    
    # Line Items
    line_items: Optional[List[Dict[str, Any]]] = Field(
        description="List of invoice line items with description, quantity, price"
    )
    
    # Additional
    notes: Optional[str] = Field(description="Additional notes or comments")
    purchase_order: Optional[str] = Field(description="Related PO number if any")

class CreditNoteContract(Contract):
    """Credit Note/Memo Data Contract"""
    credit_note_number: str = Field(description="Credit note number")
    credit_note_date: str = Field(description="Credit note date")
    original_invoice_number: str = Field(description="Reference to original invoice")
    vendor_name: str = Field(description="Vendor name")
    customer_name: Optional[str] = Field(description="Customer name")
    credit_amount: float = Field(description="Credit amount")
    reason: Optional[str] = Field(description="Reason for credit")
    currency: str = Field(default="USD", description="Currency")

class ReceiptContract(Contract):
    """Receipt/Simple Invoice Contract"""
    receipt_number: Optional[str] = Field(description="Receipt number")
    date: str = Field(description="Transaction date")
    vendor_name: str = Field(description="Store/Vendor name")
    total_amount: float = Field(description="Total amount")
    payment_method: Optional[str] = Field(description="Payment method used")
    items_purchased: Optional[List[str]] = Field(description="List of items")

# =================== Extractor Configuration ===================

class ExtractorManager:
    """Manages different extractors for various LLM providers"""
    
    def __init__(self):
        self.extractors = {}
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Initialize extractors for different LLM providers"""
        
        # Primary extractor with the chosen model
        primary_model = get_primary_model()
        self.primary_extractor = self._create_extractor(primary_model)
        
        # Backup extractors for fallback (October 2025 models - from official pricing)
        self.backup_models = [
            'gpt-5-mini',  # OpenAI GPT-5-mini (highlighted in pricing, best balance)
            'gpt-5',  # OpenAI GPT-5 (flagship)
            'claude-sonnet-4-5-20250929',  # Anthropic Claude Sonnet 4.5
            'gpt-4.1',  # OpenAI GPT-4.1
            'claude-haiku-4-5',  # Anthropic Claude Haiku 4.5 (fast)
            'gpt-4o-mini',  # OpenAI GPT-4o-mini
            'o3-mini',  # OpenAI o3-mini (reasoning)
            'ollama/llama3.3'  # Local fallback (free)
        ]
    
    def _create_extractor(self, model_name: str) -> Extractor:
        """Create an extractor with specified model"""
        extractor = Extractor()
        extractor.load_document_loader(DocumentLoaderPyPdf())
        
        try:
            extractor.load_llm(model_name)
            print(f"✅ Loaded model: {model_name}")
        except Exception as e:
            print(f"⚠️ Failed to load {model_name}: {e}")
            # Fallback to a simpler model
            extractor.load_llm("gpt-5-mini")  # Default to gpt-5-mini (highlighted in pricing)
        
        return extractor
    
    async def extract_with_fallback(
        self, 
        file_path: str, 
        contract_type: Contract
    ) -> Dict:
        """Extract data with fallback to backup models if primary fails"""
        
        # Try primary extractor
        try:
            result = self.primary_extractor.extract(file_path, contract_type)
            return {"model_used": os.getenv('PRIMARY_MODEL'), "data": result}
        except Exception as e:
            print(f"Primary extraction failed: {e}")
        
        # Try backup models
        for model in self.backup_models:
            try:
                backup_extractor = self._create_extractor(model)
                result = backup_extractor.extract(file_path, contract_type)
                return {"model_used": model, "data": result}
            except Exception as e:
                print(f"Backup {model} failed: {e}")
                continue
        
        raise HTTPException(
            status_code=500, 
            detail="All extraction methods failed"
        )

# Initialize the extractor manager
extractor_manager = ExtractorManager()

# =================== Classification System ===================

def setup_document_classifier():
    """Setup document classifier for different invoice types"""
    
    extractor = Extractor()
    extractor.load_document_loader(DocumentLoaderPyPdf())
    extractor.load_llm(get_primary_model())
    
    classifications = [
        Classification(
            name="Standard Invoice",
            description="Regular invoice with line items and tax",
            contract=InvoiceContract,
            extractor=extractor,
        ),
        Classification(
            name="Credit Note",
            description="Credit note or credit memo document",
            contract=CreditNoteContract,
            extractor=extractor,
        ),
        Classification(
            name="Receipt",
            description="Simple receipt or cash invoice",
            contract=ReceiptContract,
            extractor=extractor,
        )
    ]
    
    return extractor, classifications

# =================== API Endpoints ===================

class ProcessingRequest(BaseModel):
    """Request model for processing options"""
    use_classification: bool = Field(default=True, description="Auto-classify document type")
    extract_tables: bool = Field(default=True, description="Extract line items as tables")
    model_preference: Optional[str] = Field(default=None, description="Preferred LLM model")

class ProcessingResponse(BaseModel):
    """Response model for processed invoice"""
    status: str
    document_type: Optional[str]
    extracted_data: Dict
    model_used: str
    processing_time: float
    confidence_score: Optional[float]
    warnings: Optional[List[str]]

@app.post("/extract", response_model=ProcessingResponse)
async def extract_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: ProcessingRequest = ProcessingRequest()
):
    """
    Main endpoint for invoice extraction
    """
    start_time = datetime.now()
    warnings = []
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload PDF or image files."
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Classification (if enabled)
        document_type = "Standard Invoice"  # default
        if options.use_classification:
            classifier, classifications = setup_document_classifier()
            classification_result = classifier.classify(
                tmp_file_path,
                classifications
            )
            document_type = classification_result.name
            print(f"📄 Classified as: {document_type}")
        
        # Select appropriate contract based on classification
        contract_map = {
            "Standard Invoice": InvoiceContract,
            "Credit Note": CreditNoteContract,
            "Receipt": ReceiptContract
        }
        contract_type = contract_map.get(document_type, InvoiceContract)
        
        # Extract data with fallback
        extraction_result = await extractor_manager.extract_with_fallback(
            tmp_file_path,
            contract_type
        )
        
        # Convert to dictionary
        extracted_data = extraction_result["data"]
        if hasattr(extracted_data, 'dict'):
            extracted_data = extracted_data.dict()
        elif hasattr(extracted_data, '__dict__'):
            extracted_data = extracted_data.__dict__
        
        # Post-processing and validation
        extracted_data = post_process_invoice_data(extracted_data, warnings)
        
        # Clean up temp file
        background_tasks.add_task(cleanup_temp_file, tmp_file_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessingResponse(
            status="success",
            document_type=document_type,
            extracted_data=extracted_data,
            model_used=extraction_result["model_used"],
            processing_time=processing_time,
            confidence_score=0.95,  # You can implement actual confidence scoring
            warnings=warnings if warnings else None
        )
        
    except Exception as e:
        # Clean up on error
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@app.post("/batch_extract")
async def batch_extract(
    files: List[UploadFile] = File(...),
    options: ProcessingRequest = ProcessingRequest()
):
    """
    Batch processing for multiple invoices (simple extraction only)
    """
    results = []
    
    for file in files:
        try:
            result = await extract_invoice(
                background_tasks=BackgroundTasks(),
                file=file,
                options=options
            )
            results.append({
                "filename": file.filename,
                "result": result.dict()
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {"processed": len(files), "results": results}

@app.post("/batch_analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    full_analysis: bool = False,
    options: ProcessingRequest = ProcessingRequest()
):
    """
    Batch processing with database storage and optional full analysis
    
    Parameters:
        full_analysis: 
            - False (default): Fast extraction only (~5-7 sec/invoice)
            - True: Full CrewAI analysis (~45-55 sec/invoice)
    
    Features:
    - Extract Thinker extraction
    - Optional CrewAI validation and risk analysis
    - Automatic database storage
    - Duplicate detection (won't create duplicates)
    
    Usage:
        # Fast mode (default)
        curl -X POST "http://localhost:8000/batch_analyze" \
          -F "files=@invoice1.pdf" \
          -F "files=@invoice2.pdf"
        
        # Full analysis mode
        curl -X POST "http://localhost:8000/batch_analyze?full_analysis=true" \
          -F "files=@invoice1.pdf" \
          -F "files=@invoice2.pdf"
    """
    results = []
    successful = 0
    failed = 0
    duplicates_updated = 0
    
    for idx, file in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] Processing: {file.filename}")
        
        try:
            if full_analysis:
                # Full analysis with CrewAI (~45-55 sec)
                result = await extract_and_analyze_invoice(
                    background_tasks=BackgroundTasks(),
                    file=file,
                    options=options
                )
            else:
                # Fast extraction only (~5-7 sec)
                # Extract data
                extract_result = await extract_invoice(
                    background_tasks=BackgroundTasks(),
                    file=file,
                    options=options
                )
                
                # Convert Pydantic model to dict
                if hasattr(extract_result, 'dict'):
                    extract_dict = extract_result.dict()
                elif hasattr(extract_result, 'model_dump'):
                    extract_dict = extract_result.model_dump()
                else:
                    extract_dict = extract_result
                
                # Save to database (without CrewAI analysis)
                try:
                    invoice_id = db.save_invoice(
                        extracted_data=extract_dict["extracted_data"],
                        validation={"status": "not_analyzed"},
                        risk_analysis={"risk_level": "not_analyzed"},
                        summary="Fast extraction without analysis",
                        model_used=extract_dict["model_used"],
                        extraction_time=extract_dict["processing_time"],
                        analysis_time=0.0
                    )
                except Exception as e:
                    print(f"  Warning: Failed to save to database: {e}")
                    invoice_id = None
                
                # Format result to match expected structure
                result = {
                    "status": "success",
                    "invoice_id": invoice_id,
                    "extracted_data": extract_dict["extracted_data"],
                    "total_time_seconds": extract_dict["processing_time"],
                    "risk_analysis": {"risk_level": "not_analyzed"}
                }
            
            successful += 1
            
            # Check if it was a duplicate (ID would be same as existing)
            is_duplicate = result.get("invoice_id") is not None
            if is_duplicate:
                duplicates_updated += 1
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "invoice_id": result.get("invoice_id"),
                "invoice_number": result.get("extracted_data", {}).get("invoice_number"),
                "vendor_name": result.get("extracted_data", {}).get("vendor_name"),
                "total_amount": result.get("extracted_data", {}).get("total_amount"),
                "currency": result.get("extracted_data", {}).get("currency"),
                "risk_level": result.get("risk_analysis", {}).get("risk_level"),
                "is_duplicate": is_duplicate,
                "processing_time": result.get("total_time_seconds")
            })
            
            print(f"  ✅ Success: {result.get('extracted_data', {}).get('vendor_name')} - ${result.get('extracted_data', {}).get('total_amount')}")
            
        except Exception as e:
            failed += 1
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
            print(f"  ❌ Error: {str(e)}")
    
    return {
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "duplicates_updated": duplicates_updated,
        "results": results
    }

@app.post("/classify")
async def classify_document(file: UploadFile = File(...)):
    """
    Classify document type without extraction
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        classifier, classifications = setup_document_classifier()
        result = classifier.classify(
            tmp_file_path,
            classifications
        )
        
        return {
            "document_type": result.name,
            "confidence": result.confidence
        }
    finally:
        os.unlink(tmp_file_path)

@app.post("/extract_and_analyze")
async def extract_and_analyze_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: ProcessingRequest = ProcessingRequest()
):
    """
    Multi-agent invoice processing with CrewAI:
    1. Extract data using Extract Thinker (fast, accurate)
    2. Validate data with AI validator agent
    3. Analyze for anomalies and fraud with AI analyst agent
    4. Generate comprehensive report with AI reporter agent
    
    This endpoint provides deeper analysis and validation compared to standard extraction.
    """
    from crew_agents import process_invoice_with_crew
    
    start_time = datetime.now()
    
    # Step 1: Extract data using Extract Thinker (existing logic)
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Classify document type
        contract_type = InvoiceContract
        document_type = "invoice"
        
        if options.use_classification:
            classifier, classifications = setup_document_classifier()
            classification_result = classifier.classify(tmp_file_path, classifications)
            document_type = classification_result.name
            
            if document_type == "credit_note":
                contract_type = CreditNoteContract
            elif document_type == "receipt":
                contract_type = ReceiptContract
        
        # Extract data
        extraction_result = await extractor_manager.extract_with_fallback(
            tmp_file_path,
            contract_type
        )
        
        extracted_data = extraction_result["data"]
        model_used = extraction_result["model_used"]
        
        # Convert Pydantic model to dict if needed
        if hasattr(extracted_data, 'model_dump'):
            extracted_data_dict = extracted_data.model_dump()
        elif hasattr(extracted_data, 'dict'):
            extracted_data_dict = extracted_data.dict()
        else:
            extracted_data_dict = extracted_data
        
        # Post-process
        warnings = []
        processed_data = post_process_invoice_data(extracted_data_dict, warnings)
        
        extraction_time = (datetime.now() - start_time).total_seconds()
        
        # Step 2: Multi-agent analysis with CrewAI
        crew_start = datetime.now()
        crew_analysis = await process_invoice_with_crew(
            extracted_data=processed_data,
            confidence_scores=None  # Don't pass placeholder scores
        )
        crew_time = (datetime.now() - crew_start).total_seconds()
        
        # Combine results - simplified structure
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Save to database for analytics
        try:
            invoice_id = db.save_invoice(
                extracted_data=processed_data,
                validation=crew_analysis.get("validation", {}),
                risk_analysis=crew_analysis.get("risk_analysis", {}),
                summary=crew_analysis.get("summary", ""),
                model_used=model_used,
                extraction_time=extraction_time,
                analysis_time=crew_time
            )
        except Exception as e:
            print(f"Warning: Failed to save to database: {e}")
            invoice_id = None
        
        return {
            "status": "success",
            "invoice_id": invoice_id,
            "document_type": document_type,
            "extracted_data": processed_data,
            "model_used": model_used,
            "validation": crew_analysis.get("validation", {}),
            "risk_analysis": crew_analysis.get("risk_analysis", {}),
            "summary": crew_analysis.get("summary", ""),
            "warnings": warnings,
            "extraction_time_seconds": extraction_time,
            "analysis_time_seconds": crew_time,
            "total_time_seconds": total_time,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent processing failed: {str(e)}"
        )
    finally:
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, tmp_file_path)

# =================== Analytics Endpoints ===================

@app.get("/analytics/vendor/{vendor_name}")
async def get_vendor_invoices(
    vendor_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get all invoices from a specific vendor
    
    Example:
        /analytics/vendor/Nedstone?start_date=2025-10-01&end_date=2025-10-31
    """
    try:
        invoices = db.get_by_vendor(vendor_name, start_date, end_date)
        
        # Parse JSON fields
        for invoice in invoices:
            if invoice.get('extracted_data'):
                invoice['extracted_data'] = json.loads(invoice['extracted_data'])
            if invoice.get('validation_results'):
                invoice['validation_results'] = json.loads(invoice['validation_results'])
            if invoice.get('risk_analysis'):
                invoice['risk_analysis'] = json.loads(invoice['risk_analysis'])
        
        return {
            "vendor_name": vendor_name,
            "start_date": start_date,
            "end_date": end_date,
            "invoice_count": len(invoices),
            "invoices": invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/vendor/{vendor_name}/aggregate")
async def get_vendor_aggregate(
    vendor_name: str,
    year: Optional[int] = None
):
    """
    Get aggregate statistics for a vendor
    
    Example:
        /analytics/vendor/Nedstone/aggregate?year=2025
    """
    try:
        stats = db.aggregate_by_vendor(vendor_name, year)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/stats")
async def get_overall_stats():
    """
    Get overall database statistics
    """
    try:
        stats = db.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/high-risk")
async def get_high_risk_invoices(limit: int = 10):
    """
    Get invoices with high or medium risk
    """
    try:
        invoices = db.get_high_risk_invoices(limit)
        
        # Parse JSON fields
        for invoice in invoices:
            if invoice.get('extracted_data'):
                invoice['extracted_data'] = json.loads(invoice['extracted_data'])
            if invoice.get('risk_analysis'):
                invoice['risk_analysis'] = json.loads(invoice['risk_analysis'])
        
        return {
            "count": len(invoices),
            "invoices": invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== Chat Analytics Endpoint ===================

class ChatRequest(BaseModel):
    """Request model for chat analytics"""
    question: str = Field(..., description="Question in natural language")

class ChatResponse(BaseModel):
    """Response model for chat analytics"""
    question: str
    answer: str
    sql_query: str
    results: List[Dict]
    row_count: int
    timestamp: str

@app.post("/chat")
async def chat_analytics(request: ChatRequest):
    """
    Analytics Chat - Ask questions about invoices in natural language
    
    Examples:
        "Яка сума інвойсів від Nedstone за жовтень 2025?"
        "Скільки всього інвойсів від Atlassian?"
        "Топ 5 вендорів по сумі"
        "Які інвойси мають high risk?"
        "Середня сума інвойсу від Nedstone"
    
    The agent will:
    1. Parse your question
    2. Generate SQL query
    3. Execute on database
    4. Return natural language answer
    """
    try:
        result = await process_analytics_question(request.question)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics chat failed: {str(e)}"
        )

# =================== Helper Functions ===================

def post_process_invoice_data(data: Dict, warnings: List[str]) -> Dict:
    """
    Post-process and validate extracted data
    """
    # Check for missing critical fields
    critical_fields = ['invoice_number', 'vendor_name', 'total_amount']
    for field in critical_fields:
        if not data.get(field):
            warnings.append(f"Missing critical field: {field}")
    
    # Validate and clean financial data
    if 'total_amount' in data and data['total_amount']:
        # Ensure it's a float
        try:
            data['total_amount'] = float(str(data['total_amount']).replace(',', '').replace('$', ''))
        except:
            warnings.append("Could not parse total amount")
    
    # Calculate missing tax if we have subtotal and total
    if data.get('subtotal') and data.get('total_amount') and not data.get('tax_amount'):
        data['tax_amount'] = data['total_amount'] - data['subtotal']
        if data['subtotal'] > 0:
            data['tax_rate'] = (data['tax_amount'] / data['subtotal']) * 100
    
    # Format dates consistently
    date_fields = ['invoice_date', 'due_date']
    for field in date_fields:
        if data.get(field):
            # Try to standardize date format
            try:
                # This is simplified - you might want to use dateutil.parser
                data[field] = str(data[field])
            except:
                warnings.append(f"Could not parse date field: {field}")
    
    # Clean up None values
    data = {k: v for k, v in data.items() if v is not None}
    
    return data

def cleanup_temp_file(file_path: str):
    """Clean up temporary files"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temp file: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "invoice-extractor",
        "models_available": [
            os.getenv('PRIMARY_MODEL', 'gpt-4o-mini')
        ] + extractor_manager.backup_models
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Invoice Processing API",
        "version": "1.0.0",
        "endpoints": [
            "/extract - Extract data from single invoice",
            "/batch_extract - Process multiple invoices",
            "/classify - Classify document type",
            "/health - Service health check"
        ],
        "supported_formats": ["PDF", "PNG", "JPG", "JPEG"],
        "available_models": {
            "primary": os.getenv('PRIMARY_MODEL', 'gpt-4o-mini'),
            "backups": extractor_manager.backup_models
        }
    }

# =================== Run Server ===================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Invoice Processing Service...")
    print(f"📍 Using primary model: {get_primary_model()}")
    
    uvicorn.run(
        "invoice_service:app",  # Import string for reload support
        host="0.0.0.0",
        port=8000,
        reload=True
    )