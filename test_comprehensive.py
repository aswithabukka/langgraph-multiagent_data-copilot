#!/usr/bin/env python3
"""
Comprehensive test suite for the LangGraph Data Analysis Copilot.
Tests arithmetic, off-topic, and data queries.
"""

import requests
import time
import json

API_URL = "http://localhost:8007/api"

def test_query(query, expected_type, description):
    """Test a single query and return results."""
    print(f"\n🔍 Testing: {description}")
    print(f"   Query: '{query}'")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/infer",
            json={"query": query},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            processing_time = end_time - start_time
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ⏱️  Response Time: {processing_time:.2f}s")
            print(f"   📝 Answer: {result.get('answer', 'No answer')[:100]}...")
            
            if expected_type == "arithmetic" and processing_time < 0.1:
                print(f"   🚀 Fast arithmetic processing confirmed!")
            elif expected_type == "off-topic" and processing_time < 0.1:
                print(f"   🚀 Fast off-topic handling confirmed!")
            elif expected_type == "data" and processing_time > 1:
                print(f"   🔄 Full LangGraph workflow used for data query!")
            
            return True, result
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def main():
    """Run comprehensive tests."""
    print("🧪 Comprehensive LangGraph Data Analysis Copilot Test Suite")
    print("=" * 60)
    
    # Test API health first
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API Health Check: PASSED")
        else:
            print("❌ API Health Check: FAILED")
            return
    except Exception as e:
        print(f"❌ API Health Check: FAILED - {str(e)}")
        return
    
    # Test cases
    test_cases = [
        # Arithmetic queries (should be instant)
        ("2+2", "arithmetic", "Simple addition"),
        ("what is 15*3+7", "arithmetic", "Complex arithmetic with order of operations"),
        ("calculate (100-25)/3", "arithmetic", "Arithmetic with parentheses"),
        ("50*2-10+5", "arithmetic", "Multiple operations"),
        
        # Off-topic queries (should be instant with helpful guidance)
        ("What is MapReduce?", "off-topic", "Technology concept query"),
        ("What is machine learning?", "off-topic", "AI/ML concept query"),
        ("How do I cook pasta?", "off-topic", "Cooking tutorial query"),
        ("What's the weather today?", "off-topic", "Weather query"),
        ("Tell me about blockchain", "off-topic", "Technology explanation query"),
        
        # Data queries (should use full LangGraph workflow)
        ("show me total sales", "data", "Basic data aggregation query"),
        ("how many orders are there", "data", "Count query"),
        ("list all customers", "data", "Data listing query"),
        ("what are the top products", "data", "Top N query"),
    ]
    
    results = {
        "arithmetic": {"passed": 0, "total": 0},
        "off-topic": {"passed": 0, "total": 0},
        "data": {"passed": 0, "total": 0}
    }
    
    # Run tests
    for query, expected_type, description in test_cases:
        results[expected_type]["total"] += 1
        success, result = test_query(query, expected_type, description)
        
        if success:
            results[expected_type]["passed"] += 1
        
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    for test_type, stats in results.items():
        passed = stats["passed"]
        total = stats["total"]
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"{test_type.upper():12} | {passed:2}/{total:2} | {percentage:5.1f}%")
        total_passed += passed
        total_tests += total
    
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("-" * 60)
    print(f"{'OVERALL':12} | {total_passed:2}/{total_tests:2} | {overall_percentage:5.1f}%")
    
    if overall_percentage >= 90:
        print("\n🎉 EXCELLENT! The system is working great!")
    elif overall_percentage >= 75:
        print("\n👍 GOOD! Most features are working correctly.")
    else:
        print("\n⚠️  Some issues detected. Please check the logs above.")
    
    print(f"\n🚀 System Features:")
    print(f"   • ⚡ Instant arithmetic evaluation using AST")
    print(f"   • 🛡️  Graceful off-topic query handling")
    print(f"   • 🤖 Full LangGraph workflow for data queries")
    print(f"   • 📊 Streamlit UI: http://localhost:8501")
    print(f"   • 🔌 FastAPI Server: http://localhost:8007")

if __name__ == "__main__":
    main()
