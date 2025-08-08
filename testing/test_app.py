#!/usr/bin/env python3
"""
Test script for the Working Chatbot Application
"""

import os
import sys
import requests
import time
import json

def test_endpoint(url, method="GET", data=None, files=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("🧪 Testing Working Chatbot Application")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    result = test_endpoint(f"{base_url}/api/health")
    if result["success"]:
        print(f"✅ Health check: {result['status_code']}")
        if isinstance(result["data"], dict):
            print(f"   Status: {result['data'].get('status', 'unknown')}")
    else:
        print(f"❌ Health check failed: {result['error']}")
    
    # Test query endpoint
    print("\n2. Testing query endpoint...")
    query_data = {"query": "Hello, how are you?"}
    result = test_endpoint(f"{base_url}/api/query", method="POST", data=query_data)
    if result["success"]:
        print(f"✅ Query test: {result['status_code']}")
        if isinstance(result["data"], dict) and "answer" in result["data"]:
            print(f"   Answer: {result['data']['answer'][:100]}...")
    else:
        print(f"❌ Query test failed: {result['error']}")
    
    # Test file upload (create a test file)
    print("\n3. Testing file upload...")
    test_file_content = "This is a test document for the chatbot application. It contains sample text to test document processing and vector storage functionality."
    test_file_path = "test_document.txt"
    
    try:
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
        
        with open(test_file_path, "rb") as f:
            files = {"files": f}
            result = test_endpoint(f"{base_url}/api/upload", method="POST", files=files)
        
        if result["success"]:
            print(f"✅ File upload: {result['status_code']}")
            if isinstance(result["data"], dict):
                uploaded = result["data"].get("uploaded_files", [])
                print(f"   Uploaded files: {uploaded}")
        else:
            print(f"❌ File upload failed: {result['error']}")
        
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    except Exception as e:
        print(f"❌ File upload test error: {str(e)}")
    
    # Test query with uploaded document
    print("\n4. Testing query with document context...")
    query_data = {"query": "What is in the test document?"}
    result = test_endpoint(f"{base_url}/api/query", method="POST", data=query_data)
    if result["success"]:
        print(f"✅ Context query: {result['status_code']}")
        if isinstance(result["data"], dict):
            sources = result["data"].get("sources_used", 0)
            print(f"   Sources used: {sources}")
    else:
        print(f"❌ Context query failed: {result['error']}")
    
    # Test stats endpoint
    print("\n5. Testing stats endpoint...")
    result = test_endpoint(f"{base_url}/api/stats")
    if result["success"]:
        print(f"✅ Stats: {result['status_code']}")
    else:
        print(f"❌ Stats failed: {result['error']}")
    
    print("\n🎉 Testing complete!")
    print("\nIf all tests passed, your application is working correctly!")
    print("If some tests failed, check the server logs for more details.")

if __name__ == "__main__":
    main()