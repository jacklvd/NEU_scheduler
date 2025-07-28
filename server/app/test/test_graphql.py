import json
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def test_graphql_endpoint():
    url = "http://localhost:8000/api/graphql"
    
    # Test health check first
    health_query = {
        "query": """
        query {
            healthCheck
        }
        """
    }
    
    print("Testing health check...")
    try:
        req = Request(url, 
                     data=json.dumps(health_query).encode('utf-8'),
                     headers={'Content-Type': 'application/json'})
        
        response = urlopen(req, timeout=10)
        print(f"Health check status: {response.status}")
        
        data = json.loads(response.read().decode('utf-8'))
        print(f"Health check response: {data}")
        
    except Exception as e:
        print(f"Health check error: {e}")
        return
    
    # Test AI suggestion
    ai_query = {
        "query": """
        query {
            suggestPlan(interest: "machine learning", years: 2) {
                year
                term
                courses
                credits
                notes
            }
        }
        """
    }
    
    print("\nTesting AI suggestion (this may take a moment)...")
    try:
        req = Request(url, 
                     data=json.dumps(ai_query).encode('utf-8'),
                     headers={'Content-Type': 'application/json'})
        
        start_time = time.time()
        response = urlopen(req, timeout=120)  # 2 minute timeout
        end_time = time.time()
        
        print(f"AI suggestion status: {response.status}")
        print(f"Response time: {end_time - start_time:.2f} seconds")
        
        data = json.loads(response.read().decode('utf-8'))
        print(f"AI suggestion response: {json.dumps(data, indent=2)}")
        
    except Exception as e:
        print(f"AI suggestion error: {e}")

if __name__ == "__main__":
    test_graphql_endpoint()
