import asyncio
import aiohttp
import json
from pathlib import Path

async def test_single_extraction():
    """Test single invoice extraction"""
    
    # Your test invoice file
    test_file = "test_invoice.pdf"
    
    async with aiohttp.ClientSession() as session:
        with open(test_file, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file',
                          f,
                          filename=test_file,
                          content_type='application/pdf')
            
            # Add options
            data.add_field('options', json.dumps({
                "use_classification": True,
                "extract_tables": True
            }))
            
            async with session.post('http://localhost:8000/extract', data=data) as resp:
                result = await resp.json()
                
                if resp.status == 200:
                    print("✅ Extraction successful!")
                    print(f"📄 Document Type: {result['document_type']}")
                    print(f"🤖 Model Used: {result['model_used']}")
                    print(f"⏱️ Processing Time: {result['processing_time']}s")
                    print("\n📊 Extracted Data:")
                    print(json.dumps(result['extracted_data'], indent=2))
                    
                    # Validate key fields
                    data = result['extracted_data']
                    assert data.get('invoice_number'), "Invoice number missing"
                    assert data.get('vendor_name'), "Vendor name missing"
                    assert data.get('total_amount'), "Total amount missing"
                    
                    print("\n✅ All validations passed!")
                else:
                    print(f"❌ Error: {result}")

async def test_batch_extraction():
    """Test batch extraction"""
    
    test_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        
        for file_path in test_files:
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    data.add_field('files',
                                  f.read(),
                                  filename=file_path,
                                  content_type='application/pdf')
        
        async with session.post('http://localhost:8000/batch_extract', data=data) as resp:
            result = await resp.json()
            print(f"✅ Processed {result['processed']} files")
            
            for file_result in result['results']:
                print(f"\n📄 {file_result['filename']}:")
                if 'error' in file_result:
                    print(f"  ❌ Error: {file_result['error']}")
                else:
                    print(f"  ✅ Success - {file_result['result']['document_type']}")

async def test_classification():
    """Test document classification"""
    
    test_file = "test_invoice.pdf"
    
    async with aiohttp.ClientSession() as session:
        with open(test_file, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file',
                          f,
                          filename=test_file,
                          content_type='application/pdf')
            
            async with session.post('http://localhost:8000/classify', data=data) as resp:
                result = await resp.json()
                print(f"📄 Document Type: {result['document_type']}")
                print(f"🎯 Confidence: {result['confidence']}")

async def main():
    print("🧪 Testing Invoice Extraction System\n")
    print("=" * 50)
    
    print("\n1️⃣ Testing Single Extraction:")
    await test_single_extraction()
    
    print("\n" + "=" * 50)
    print("\n2️⃣ Testing Document Classification:")
    await test_classification()
    
    print("\n" + "=" * 50)
    print("\n3️⃣ Testing Batch Extraction:")
    # await test_batch_extraction()

if __name__ == "__main__":
    asyncio.run(main())