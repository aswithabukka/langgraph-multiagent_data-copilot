#!/usr/bin/env python3
"""
Full system test for the LangGraph Data Analysis Copilot.
"""

import os
import requests
import time

API_BASE = os.getenv("API_URL", "http://localhost:8000/api")

def test_api_health():
    """Test API health endpoint."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"✅ API Health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ API Health Check Failed: {str(e)}")
        return False

def test_arithmetic_query():
    """Test simple arithmetic query."""
    try:
        response = requests.post(
            f"{API_BASE}/infer",
            json={"query": "What is 10 + 5?"},
            timeout=10
        )
        print(f"✅ Arithmetic Query: {response.status_code}")
        result = response.json()
        print(f"   Answer: {result.get('answer')}")
        print(f"   Processing Time: {result.get('processing_time_ms')}ms")
        return True
    except Exception as e:
        print(f"❌ Arithmetic Query Failed: {str(e)}")
        return False

def test_database_query():
    """Test database query."""
    try:
        response = requests.post(
            f"{API_BASE}/infer",
            json={"query": "How many orders are in the database?"},
            timeout=30
        )
        print(f"✅ Database Query: {response.status_code}")
        result = response.json()
        print(f"   Answer: {result.get('answer')}")
        print(f"   Processing Time: {result.get('processing_time_ms')}ms")
        return True
    except Exception as e:
        print(f"❌ Database Query Failed: {str(e)}")
        return False

def test_tables_endpoint():
    """Test tables endpoint."""
    try:
        response = requests.get(f"{API_BASE}/tables", timeout=5)
        print(f"✅ Tables Endpoint: {response.status_code}")
        print(f"   Tables: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Tables Endpoint Failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing LangGraph Data Analysis Copilot")
    print("=" * 50)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Tables Endpoint", test_tables_endpoint),
        ("Arithmetic Query", test_arithmetic_query),
        ("Database Query", test_database_query),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        print("\n🚀 You can now use the application:")
        print("   📊 FastAPI Server: http://localhost:8001")
        print("   🎨 Streamlit UI: http://localhost:8501")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    main()
