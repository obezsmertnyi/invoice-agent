"""
Example: Using Multi-Agent Invoice Processing
Demonstrates both standard extraction and multi-agent analysis
"""

import requests
import json
from pathlib import Path


# API Configuration
API_BASE_URL = "http://localhost:8000"


def example_standard_extraction(invoice_path: str):
    """
    Example 1: Standard extraction (fast, cost-effective)
    Use for routine invoice processing
    """
    print("=" * 60)
    print("EXAMPLE 1: Standard Extraction (Extract Thinker only)")
    print("=" * 60)
    
    with open(invoice_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE_URL}/extract",
            files={'file': f},
            json={
                'use_classification': True,
                'extract_tables': True
            }
        )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Status: {result['status']}")
        print(f"📄 Document Type: {result['document_type']}")
        print(f"🤖 Model Used: {result['model_used']}")
        print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
        
        data = result['extracted_data']
        print(f"\n📊 Extracted Data:")
        print(f"  Invoice #: {data.get('invoice_number', 'N/A')}")
        print(f"  Vendor: {data.get('vendor_name', 'N/A')}")
        print(f"  Date: {data.get('invoice_date', 'N/A')}")
        print(f"  Amount: ${data.get('total_amount', 0):,.2f}")
        
        if result.get('warnings'):
            print(f"\n⚠️  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"    - {warning}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def example_multi_agent_analysis(invoice_path: str):
    """
    Example 2: Multi-agent analysis (comprehensive)
    Use for high-value invoices or when validation/fraud detection is needed
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Multi-Agent Analysis (Extract Thinker + CrewAI)")
    print("=" * 60)
    
    with open(invoice_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE_URL}/extract_and_analyze",
            files={'file': f},
            json={
                'use_classification': True,
                'extract_tables': True
            }
        )
    
    if response.status_code == 200:
        result = response.json()
        
        # Extraction Results
        print(f"\n✅ Status: {result['status']}")
        print(f"📄 Document Type: {result['document_type']}")
        
        extraction = result['extraction']
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"  Model: {extraction['model_used']}")
        print(f"  Time: {extraction['extraction_time']:.2f}s")
        
        data = extraction['data']
        print(f"\n  Extracted Data:")
        print(f"    Invoice #: {data.get('invoice_number', 'N/A')}")
        print(f"    Vendor: {data.get('vendor_name', 'N/A')}")
        print(f"    Date: {data.get('invoice_date', 'N/A')}")
        print(f"    Amount: ${data.get('total_amount', 0):,.2f}")
        print(f"    Currency: {data.get('currency', 'USD')}")
        
        # Validation Results
        crew = result['crew_analysis']
        validation = crew['validation']
        
        print(f"\n🔍 VALIDATION RESULTS:")
        print(f"  Status: {validation['status'].upper()}")
        print(f"  Fields Checked: {validation['fields_checked']}")
        
        if validation['issues']:
            print(f"\n  ❌ Issues Found ({len(validation['issues'])}):")
            for issue in validation['issues']:
                print(f"    - {issue}")
        else:
            print(f"  ✅ No issues found")
        
        if validation['warnings']:
            print(f"\n  ⚠️  Warnings ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"    - {warning}")
        
        # Risk Analysis
        risk = crew['risk_analysis']
        
        print(f"\n🚨 RISK ANALYSIS:")
        print(f"  Risk Level: {risk['risk_level'].upper()}")
        print(f"  Risk Score: {risk['risk_score']}/10")
        print(f"  Anomalies Found: {risk['anomalies_found']}")
        
        if risk['anomalies']:
            print(f"\n  Detected Anomalies:")
            for anomaly in risk['anomalies']:
                severity_emoji = {
                    'low': '🟡',
                    'medium': '🟠',
                    'high': '🔴'
                }.get(anomaly['severity'], '⚪')
                
                print(f"    {severity_emoji} [{anomaly['severity'].upper()}] {anomaly['type']}")
                print(f"       {anomaly['description']}")
                print(f"       → {anomaly['recommendation']}")
        
        print(f"\n  📋 Recommendation:")
        print(f"    {risk['recommendation']}")
        
        # Summary Report
        print(f"\n📝 EXECUTIVE SUMMARY:")
        summary_lines = crew['summary'].split('\n')
        for line in summary_lines[:5]:  # First 5 lines
            if line.strip():
                print(f"  {line.strip()}")
        
        # Timing
        timing = result['timing']
        print(f"\n⏱️  PERFORMANCE:")
        print(f"  Extraction: {timing['extraction_time_seconds']:.2f}s")
        print(f"  Crew Analysis: {timing['crew_analysis_time_seconds']:.2f}s")
        print(f"  Total: {timing['total_time_seconds']:.2f}s")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def example_comparison(invoice_path: str):
    """
    Example 3: Compare both approaches
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Comparison - Standard vs Multi-Agent")
    print("=" * 60)
    
    # Standard extraction
    with open(invoice_path, 'rb') as f:
        standard_response = requests.post(
            f"{API_BASE_URL}/extract",
            files={'file': f}
        )
    
    # Multi-agent analysis
    with open(invoice_path, 'rb') as f:
        crew_response = requests.post(
            f"{API_BASE_URL}/extract_and_analyze",
            files={'file': f}
        )
    
    if standard_response.status_code == 200 and crew_response.status_code == 200:
        standard = standard_response.json()
        crew = crew_response.json()
        
        print(f"\n📊 COMPARISON:")
        print(f"\n  Standard Extraction:")
        print(f"    Time: {standard['processing_time']:.2f}s")
        print(f"    Output: Basic data extraction")
        print(f"    Use case: Routine invoices")
        
        print(f"\n  Multi-Agent Analysis:")
        print(f"    Time: {crew['timing']['total_time_seconds']:.2f}s")
        print(f"    Output: Extraction + Validation + Risk Analysis + Report")
        print(f"    Use case: High-value invoices, compliance")
        
        print(f"\n  Speed Difference: {crew['timing']['total_time_seconds'] / standard['processing_time']:.1f}x slower")
        print(f"  Value Added: Validation, fraud detection, risk assessment")


def example_batch_processing():
    """
    Example 4: Batch processing with intelligent routing
    Route invoices to appropriate endpoint based on amount
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Intelligent Batch Processing")
    print("=" * 60)
    
    invoices = [
        {"path": "invoice1.pdf", "expected_amount": 500},
        {"path": "invoice2.pdf", "expected_amount": 25000},
        {"path": "invoice3.pdf", "expected_amount": 1200},
    ]
    
    HIGH_VALUE_THRESHOLD = 10000
    
    for invoice in invoices:
        print(f"\n📄 Processing: {invoice['path']}")
        print(f"   Expected Amount: ${invoice['expected_amount']:,.2f}")
        
        # Route based on expected amount
        if invoice['expected_amount'] > HIGH_VALUE_THRESHOLD:
            print(f"   → Routing to: Multi-Agent Analysis (high value)")
            endpoint = "/extract_and_analyze"
        else:
            print(f"   → Routing to: Standard Extraction (routine)")
            endpoint = "/extract"
        
        # In real scenario, would make actual API call here
        print(f"   ✅ Would call: {API_BASE_URL}{endpoint}")


if __name__ == "__main__":
    # Example invoice path (replace with your actual invoice)
    INVOICE_PATH = "sample_invoice.pdf"
    
    # Check if file exists
    if not Path(INVOICE_PATH).exists():
        print(f"⚠️  Sample invoice not found: {INVOICE_PATH}")
        print(f"Please provide a valid invoice PDF path")
        print(f"\nUsage:")
        print(f"  python example_crew_usage.py")
        print(f"\nOr modify INVOICE_PATH in the script")
    else:
        # Run examples
        example_standard_extraction(INVOICE_PATH)
        example_multi_agent_analysis(INVOICE_PATH)
        example_comparison(INVOICE_PATH)
        example_batch_processing()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
