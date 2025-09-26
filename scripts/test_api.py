"""
Test script to check API connectivity.
"""

import requests

API_URL = "http://localhost:8090/api"

def test_health():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Health Status Code: {response.status_code}")
        print(f"Health Response: {response.json()}")
    except Exception as e:
        print(f"Health Error: {str(e)}")

def test_tables():
    """Test the tables endpoint."""
    try:
        response = requests.get(f"{API_URL}/tables")
        print(f"Tables Status Code: {response.status_code}")
        print(f"Tables Response: {response.json()}")
    except Exception as e:
        print(f"Tables Error: {str(e)}")

def test_infer():
    """Test the infer endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/infer",
            json={"query": "What is 2+2?"},
            timeout=10,
        )
        print(f"Infer Status Code: {response.status_code}")
        print(f"Infer Response: {response.json()}")
    except Exception as e:
        print(f"Infer Error: {str(e)}")

if __name__ == "__main__":
    print("Testing API connectivity...")
    test_health()
    print("\nTesting tables endpoint...")
    test_tables()
    print("\nTesting infer endpoint...")
    test_infer()
