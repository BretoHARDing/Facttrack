import httpx
import json

base_url = "http://localhost:8000"

def test_ai_pipeline():
    print("🚀 FACTTRACK End-to-End AI Validation Script")
    print("-" * 50)
    
    with httpx.Client(base_url=base_url) as client:
        # 1. Register or Login
        print("[1] Authenticating user...")
        resp = client.post("/api/v1/auth/register", json={
            "email": "ai_tester@facttrack.io",
            "password": "SecurePassword123!",
            "display_name": "AI Tester"
        })
        
        # If user exists (409), just login
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "ai_tester@facttrack.io",
            "password": "SecurePassword123!"
        })
        
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            print(f"✅ Authentication successful. Token obtained.")
        else:
            print(f"❌ Auth failed: {login_resp.text}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test Contradiction (High Probability)
        print("\n[2] Testing AI Engine (Contradiction Case)...")
        claim1 = "The suspect drove a red car on Tuesday."
        claim2 = "The suspect did not drive a red car on Tuesday."
        print(f"Claim 1: {claim1}")
        print(f"Claim 2: {claim2}")
        
        ai_resp1 = client.post("/api/v1/ai/contradiction", headers=headers, json={
            "claim1": claim1,
            "claim2": claim2
        })
        
        if ai_resp1.status_code == 200:
            print(f"Result: {json.dumps(ai_resp1.json(), indent=2)}")
        else:
            print(f"Error {ai_resp1.status_code}: {ai_resp1.text}")
        
        # 3. Test Non-Contradiction (Low Probability)
        print("\n[3] Testing AI Engine (Agreement Case)...")
        claim3 = "The suspect was wearing a blue jacket."
        claim4 = "The suspect had a blue jacket on."
        print(f"Claim 1: {claim3}")
        print(f"Claim 2: {claim4}")
        
        ai_resp2 = client.post("/api/v1/ai/contradiction", headers=headers, json={
            "claim1": claim3,
            "claim2": claim4
        })
        
        if ai_resp2.status_code == 200:
            print(f"Result: {json.dumps(ai_resp2.json(), indent=2)}")
        else:
            print(f"Error {ai_resp2.status_code}: {ai_resp2.text}")

if __name__ == "__main__":
    test_ai_pipeline()
