import httpx
import random
import sys
from PIL import Image
import io

BASE_URL = "http://127.0.0.1:8000/api/v1"

rand_id = random.randint(1000, 9999)
email_a = f"plan_chat_a_{rand_id}@example.com"
email_b = f"plan_chat_b_{rand_id}@example.com"
password = "Password@123"

client_a = httpx.Client(timeout=30.0)
client_b = httpx.Client(timeout=30.0)

def register_and_login(email, client):
    # 1. Register
    reg_payload = {
        "full_name": f"Tester {email.split('@')[0]}",
        "email": email,
        "password": password
    }
    reg_resp = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    
    # 2. Login
    login_payload = {
        "email": email,
        "password": password
    }
    login_resp = client.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    print(f"[OK] Registered and logged in user: {email}")

def create_plan_for_user(client):
    # 1. Upload skin scan
    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    dummy_png = img_byte_arr.getvalue()
    files = {"file": ("test_face.png", dummy_png, "image/png")}
    
    resp = client.post(f"{BASE_URL}/predict", files=files)
    assert resp.status_code == 200, f"Scan failed: {resp.text}"
    pred_id = resp.json()["prediction_id"]
    
    # 2. Generate plan
    plan_payload = {
        "prediction_id": pred_id,
        "dosha_answers": {
            "body_frame": "small_thin",
            "hunger": "irregular",
            "sleep": "light",
            "feeling": "cold",
            "digestion": "gas_bloat",
            "mood": "quick_anxious"
        },
        "skin_type": "dry",
        "age_group": "21-30",
        "season": "winter",
        "lifestyle": ["poor_sleep"]
    }
    
    plan_resp = client.post(f"{BASE_URL}/plan/generate", json=plan_payload)
    assert plan_resp.status_code == 200, f"Plan generation failed: {plan_resp.text}"
    plan_data = plan_resp.json()
    print(f"[OK] Generated plan '{plan_data['title']}' for user.")
    return plan_data["id"]

def main():
    print("=== STARTING MY PLAN CHAT MODE INTEGRATION TESTS ===")
    
    # Register and Login User A and User B
    register_and_login(email_a, client_a)
    register_and_login(email_b, client_b)
    
    # Create plan for User A
    plan_id_a = create_plan_for_user(client_a)
    
    # 1. Test GET /chat/plans for User A (Should include User A's plan)
    print("\n[TEST 1] Fetching plans list for User A...")
    plans_resp_a = client_a.get(f"{BASE_URL}/chat/plans")
    assert plans_resp_a.status_code == 200, f"Failed: {plans_resp_a.text}"
    plans_a = plans_resp_a.json()
    assert len(plans_a) > 0, "User A should have at least one plan."
    
    # Verify plan list shape
    user_a_plan = next((p for p in plans_a if p["id"] == plan_id_a), None)
    assert user_a_plan is not None, "User A's plan should be in the list."
    assert "title" in user_a_plan
    assert "condition" in user_a_plan
    assert "dosha" in user_a_plan
    assert "created_at" in user_a_plan
    # Verify creation date format (YYYY-MM-DD)
    assert len(user_a_plan["created_at"]) == 10 and user_a_plan["created_at"][4] == '-' and user_a_plan["created_at"][7] == '-'
    print(f"[OK] User A's plans list returned successfully. Match: {user_a_plan}")

    # 2. Test GET /chat/plans for User B (Should NOT include User A's plan)
    print("\n[TEST 2] Fetching plans list for User B...")
    plans_resp_b = client_b.get(f"{BASE_URL}/chat/plans")
    assert plans_resp_b.status_code == 200, f"Failed: {plans_resp_b.text}"
    plans_b = plans_resp_b.json()
    assert not any(p["id"] == plan_id_a for p in plans_b), "User B should not see User A's plan."
    print("[OK] User B's plans list does not leak User A's plan.")

    # 3. Test Authorized Plan Chat Mode (User A chats with their own plan)
    print("\n[TEST 3] Sending chat in plan mode for User A (Authorized)...")
    chat_payload_a = {
        "message": "Why was Neem recommended?",
        "history": [],
        "chat_mode": "plan",
        "plan_id": plan_id_a
    }
    chat_resp_a = client_a.post(f"{BASE_URL}/chat", json=chat_payload_a)
    assert chat_resp_a.status_code == 200, f"Chat failed: {chat_resp_a.text}"
    chat_data_a = chat_resp_a.json()
    assert "answer" in chat_data_a
    print(f"[OK] Chat answered: {chat_data_a['answer'][:120]}...")

    # 4. Test Unauthorized Plan Chat Mode (User B chats with User A's plan)
    print("\n[TEST 4] Sending chat in plan mode for User B with User A's plan (Unauthorized)...")
    chat_payload_b = {
        "message": "Why was Neem recommended?",
        "history": [],
        "chat_mode": "plan",
        "plan_id": plan_id_a
    }
    chat_resp_b = client_b.post(f"{BASE_URL}/chat", json=chat_payload_b)
    print(f"Status: {chat_resp_b.status_code}")
    assert chat_resp_b.status_code == 403, f"Expected 403 Forbidden, got {chat_resp_b.status_code}: {chat_resp_b.text}"
    print("[OK] Correctly rejected unauthorized plan access with 403 Forbidden.")

    # 5. Test Chat Mode with Invalid plan_id format
    print("\n[TEST 5] Sending chat in plan mode with invalid plan_id format...")
    chat_payload_invalid = {
        "message": "Why was Neem recommended?",
        "history": [],
        "chat_mode": "plan",
        "plan_id": "invalid_id_123"
    }
    chat_resp_invalid = client_a.post(f"{BASE_URL}/chat", json=chat_payload_invalid)
    print(f"Status: {chat_resp_invalid.status_code}")
    assert chat_resp_invalid.status_code == 404, f"Expected 404 Not Found, got {chat_resp_invalid.status_code}: {chat_resp_invalid.text}"
    print("[OK] Correctly rejected invalid plan ID format with 404 Not Found.")

    print("\n=== ALL MY PLAN CHAT MODE TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        sys.exit(1)
