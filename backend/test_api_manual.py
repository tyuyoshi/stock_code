"""Manual API test script"""

import requests
import json
from datetime import datetime

def test_api():
    """Test Stock Price API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Stock Price API Endpoints")
    print("=" * 50)
    
    try:
        # Test health check first
        print("1. Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return
        
        # Test latest price endpoint
        print("\n2. Testing latest price endpoint for 7203...")
        response = requests.get(f"{base_url}/api/v1/stock-prices/7203/latest", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Current price: ¥{data.get('current_price', 'N/A')}")
            print(f"   📊 Volume: {data.get('volume', 'N/A'):,}")
            print(f"   📅 Last updated: {data.get('last_updated', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.text}")
        
        # Test historical data endpoint
        print("\n3. Testing historical data endpoint...")
        response = requests.get(f"{base_url}/api/v1/stock-prices/7203/historical?days=5", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Records returned: {len(data)}")
            if data:
                latest = data[0]
                print(f"   📈 Latest record: {latest.get('date')} - ¥{latest.get('close_price', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.text}")
        
        # Test chart data endpoint
        print("\n4. Testing chart data endpoint...")
        response = requests.get(f"{base_url}/api/v1/stock-prices/7203/chart?period=1mo", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Chart points: {len(data.get('data', []))}")
            print(f"   📊 Period: {data.get('period', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.text}")
        
        # Test multiple tickers endpoint
        print("\n5. Testing multiple tickers endpoint...")
        response = requests.get(f"{base_url}/api/v1/stock-prices/?tickers=7203&tickers=9984", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Records returned: {len(data)}")
            for record in data[:2]:  # Show first 2
                print(f"   📈 {record.get('ticker_symbol')}: ¥{record.get('close_price', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.text}")
        
        # Test live data endpoint
        print("\n6. Testing live data endpoint...")
        response = requests.get(f"{base_url}/api/v1/stock-prices/7203/latest?live=true", timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Live price: ¥{data.get('current_price', 'N/A')}")
            print(f"   🔄 Change: {data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)")
        else:
            print(f"   ❌ Failed: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure the API server is running on localhost:8000")
        print("   Start the server with: uvicorn api.main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n🏁 API testing completed!")

if __name__ == "__main__":
    test_api()