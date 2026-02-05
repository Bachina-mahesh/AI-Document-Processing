"""
test_api.py - API Testing Script
This script tests all endpoints of the document processing system
"""

import requests
import time
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
SAMPLE_DOCS_DIR = "sample_documents"

def print_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_health_check():
    """Test the health check endpoint"""
    print_header("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Server is healthy!")
            print(f"\n   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   LLM: {data.get('llm')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server!")
        print_info("Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_upload_document(filename: str):
    """Test document upload endpoint"""
    print_header(f"2. Uploading Document: {filename}")
    
    try:
        filepath = Path(SAMPLE_DOCS_DIR) / filename
        
        if not filepath.exists():
            print_error(f"File not found: {filepath}")
            print_info("Run 'python create_samples.py' to create sample documents")
            return None
        
        print_info(f"Reading file: {filepath}")
        
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            doc_id = result['document_id']
            
            print_success("Document uploaded successfully!")
            print(f"\n   Document ID: {doc_id}")
            print(f"   Filename: {filename}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            
            return doc_id
        else:
            print_error(f"Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None

def test_check_status(doc_id: str, max_checks: int = 10):
    """Test status checking endpoint"""
    print_header("3. Checking Processing Status")
    
    try:
        for i in range(max_checks):
            response = requests.get(
                f"{BASE_URL}/api/v1/documents/{doc_id}/status"
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                print(f"\n   Check {i+1}/{max_checks}:")
                print(f"   Status: {status}")
                print(f"   Filename: {data.get('filename')}")
                
                if status in ['completed', 'failed', 'partial']:
                    print_success(f"Processing finished with status: {status}")
                    return status
                elif status == 'processing':
                    print_info("Still processing... waiting 10 seconds")
                    time.sleep(10)
                else:  # pending
                    print_info("Pending... waiting 10 seconds")
                    time.sleep(10)
            else:
                print_error(f"Status check failed: {response.status_code}")
                return None
        
        print_info(f"Status still not final after {max_checks} checks")
        return None
        
    except Exception as e:
        print_error(f"Status check error: {e}")
        return None

def test_get_results(doc_id: str):
    """Test results retrieval endpoint"""
    print_header("4. Retrieving Processing Results")
    
    try:
        print_info("Waiting 30 seconds for processing to complete...")
        time.sleep(30)
        
        response = requests.get(
            f"{BASE_URL}/api/v1/documents/{doc_id}/results"
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print_success("Results retrieved successfully!")
            print("\n" + "-" * 70)
            
            # Classification
            if result.get('classification'):
                cls = result['classification']
                print("\n📊 CLASSIFICATION:")
                print(f"   Document Type: {cls.get('document_type')}")
                print(f"   Confidence: {cls.get('confidence', 0):.2%}")
                print(f"   Reasoning: {cls.get('reasoning', 'N/A')[:100]}...")
            
            # Extraction
            if result.get('extraction'):
                ext = result['extraction']
                print("\n📝 EXTRACTION:")
                fields = ext.get('fields', {})
                print(f"   Fields Extracted: {len(fields)}")
                for key, value in list(fields.items())[:5]:
                    print(f"   - {key}: {value}")
                if len(fields) > 5:
                    print(f"   ... and {len(fields) - 5} more fields")
                print(f"   Confidence: {ext.get('confidence', 0):.2%}")
            
            # Validation
            if result.get('validation'):
                val = result['validation']
                print("\n✓ VALIDATION:")
                print(f"   Is Valid: {val.get('is_valid')}")
                print(f"   Confidence: {val.get('confidence', 0):.2%}")
                if val.get('conflicts'):
                    print(f"   Conflicts Found: {len(val['conflicts'])}")
                if val.get('missing_fields'):
                    print(f"   Missing Fields: {', '.join(val['missing_fields'])}")
            
            # Routing
            if result.get('routing'):
                route = result['routing']
                print("\n🎯 ROUTING:")
                print(f"   Destination: {route.get('destination')}")
                print(f"   Human Review Required: {route.get('requires_human_review')}")
                print(f"   Confidence: {route.get('confidence', 0):.2%}")
                print(f"   Reasoning: {route.get('reasoning', 'N/A')[:100]}...")
            
            # Processing Info
            print("\n⏱️  PROCESSING INFO:")
            print(f"   Status: {result.get('status')}")
            print(f"   Processing Time: {result.get('processing_time', 0):.1f}s")
            if result.get('errors'):
                print(f"   Errors: {len(result['errors'])}")
            
            print("\n" + "-" * 70)
            
            return result
            
        elif response.status_code == 202:
            print_info("Document still processing. Try again in a moment.")
            return None
        else:
            print_error(f"Failed to get results: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error getting results: {e}")
        return None

def test_list_documents():
    """Test document listing endpoint"""
    print_header("5. Listing All Documents")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents")
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Found {data['total']} document(s)")
            print(f"\n   Total: {data['total']}")
            print(f"   Processing: {data.get('processing', 0)}")
            print(f"   Completed: {data.get('completed', 0)}")
            
            if data['documents']:
                print("\n   Documents:")
                for doc in data['documents']:
                    print(f"   - {doc['filename']}: {doc['status']}")
            
            return data
        else:
            print_error(f"Failed to list documents: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error listing documents: {e}")
        return None

def run_full_test(filename: str = "invoice.txt"):
    """Run complete test suite"""
    print("\n" + "=" * 70)
    print("  🚀 DOCUMENT PROCESSING SYSTEM - API TEST SUITE")
    print("=" * 70)
    print(f"\n  Testing with file: {filename}")
    print(f"  Target: {BASE_URL}")
    print("\n" + "=" * 70)
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Server is not reachable. Aborting tests.")
        return False
    
    time.sleep(2)
    
    # Test 2: Upload Document
    doc_id = test_upload_document(filename)
    if not doc_id:
        print("\n❌ Upload failed. Aborting tests.")
        return False
    
    time.sleep(2)
    
    # Test 3: Check Status
    final_status = test_check_status(doc_id)
    
    time.sleep(2)
    
    # Test 4: Get Results
    results = test_get_results(doc_id)
    
    time.sleep(2)
    
    # Test 5: List Documents
    test_list_documents()
    
    # Summary
    print_header("TEST SUMMARY")
    
    if results and final_status == 'completed':
        print_success("All tests passed successfully! 🎉")
        print("\nYour document processing system is working correctly!")
        return True
    else:
        print_error("Some tests failed or processing incomplete")
        return False

if __name__ == "__main__":
    run_full_test("invoice.txt")