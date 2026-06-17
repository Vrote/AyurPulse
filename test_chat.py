import httpx
import random

BASE_URL = "http://127.0.0.1:8000/api/v1"
rand_id = random.randint(1000, 9999)
email = f"chat_tester_{rand_id}@example.com"
password = "Password@123"

client = httpx.Client(timeout=120.0)  # Extended: first chat request cold-loads HF embedding model (~60-90s)

def main():
    print("=== Testing RAG Chatbot Endpoint ===")
    
    # 1. Register
    reg_payload = {
        "full_name": "Chat Tester",
        "email": email,
        "password": password
    }
    print(f"Registering patient: {email}")
    reg_resp = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    
    # 2. Login
    login_payload = {
        "email": email,
        "password": password
    }
    print("Logging in...")
    login_resp = client.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    
    client.headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Chat query
    chat_payload = {
        "message": "What cooling herbs are good for Pitta?"
    }
    print("Sending chat message: 'What cooling herbs are good for Pitta?'")
    chat_resp = client.post(f"{BASE_URL}/chat", json=chat_payload)
    print(f"Status: {chat_resp.status_code}")
    
    chat_data = chat_resp.json()
    print("Response payload:")
    import json
    print(json.dumps(chat_data, indent=2))
    
    # 4. Verify structural response
    assert "answer" in chat_data, "Response missing 'answer' field"
    assert "sources" in chat_data, "Response missing 'sources' field"
    
    # Verify that sources is empty (since RAG is removed)
    sources = chat_data["sources"]
    assert len(sources) == 0, "Expected sources to be empty as RAG is removed!"
    print("[OK] Verified sources is empty as RAG is removed.")
    
    print("[OK] Non-RAG Chatbot response verified successfully.")

if __name__ == "__main__":
    main()
