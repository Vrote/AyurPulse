import httpx
import time
import random
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Generate unique accounts for this run
rand_id = random.randint(1000, 9999)
patient_email = f"patient_{rand_id}@example.com"
doctor_email = f"doctor_{rand_id}@example.com"
password = "Password@123"

print("="*60)
print(f"STARTING COMPREHENSIVE INTEGRATION & DB VERIFICATION TEST")
print(f"Target URL: {BASE_URL}")
print(f"Patient Email: {patient_email}")
print(f"Doctor Email: {doctor_email}")
print("="*60)

client = httpx.Client(timeout=30.0)

def test_patient_registration():
    print("\n[STEP 1] Testing Patient Registration...")
    payload = {
        "full_name": "John Patient",
        "email": patient_email,
        "password": password
    }
    response = client.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 201, f"Failed: {res_data}"
    assert res_data["status"] == "success"
    assert res_data["user"]["email"] == patient_email
    assert res_data["user"]["role"] == "user"
    print("[OK] Patient Registration verified successfully.")

def test_doctor_registration():
    print("\n[STEP 2] Testing Doctor Registration...")
    payload = {
        "full_name": "Dr. Ayur Expert",
        "email": doctor_email,
        "password": password,
        "specialization": "Ayurvedic Dermatology",
        "clinic_address": "456 Veda Boulevard, Pune",
        "experience_years": 12
    }
    response = client.post(f"{BASE_URL}/auth/doctor/register", json=payload)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 201, f"Failed: {res_data}"
    assert res_data["status"] == "success"
    assert res_data["user"]["email"] == doctor_email
    assert res_data["user"]["role"] == "doctor"
    print("[OK] Doctor Registration verified successfully.")

def test_patient_login_and_profile():
    print("\n[STEP 3] Testing Patient Login and Profile Retrieval...")
    payload = {
        "email": patient_email,
        "password": password
    }
    response = client.post(f"{BASE_URL}/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 200, f"Failed: {res_data}"
    access_token = res_data["access_token"]
    
    # Store access token in client headers
    client.headers = {"Authorization": f"Bearer {access_token}"}
    
    # Fetch profile
    me_resp = client.get(f"{BASE_URL}/auth/me")
    print(f"Get Profile Status: {me_resp.status_code}")
    me_data = me_resp.json()
    assert me_resp.status_code == 200, f"Failed: {me_data}"
    assert me_data["email"] == patient_email
    assert me_data["role"] == "user"
    print("[OK] Patient login and '/auth/me' profiles matched.")

def test_skin_analysis_upload():
    print("\n[STEP 4] Testing PyTorch Skin Scan Analysis Upload...")
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    dummy_png = img_byte_arr.getvalue()
    
    files = {"file": ("test_face.png", dummy_png, "image/png")}
    response = client.post(f"{BASE_URL}/predict", files=files)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 200, f"Failed: {res_data}"
    assert "prediction_id" in res_data
    assert "detected_conditions" in res_data
    print(f"[OK] AI Skin Diagnostic outputs received: {res_data['detected_conditions']}")
    return res_data["prediction_id"]

def test_generate_plan(prediction_id):
    print("\n[STEP 5] Testing personalized 7-day treatment plan generation...")
    payload = {
        "prediction_id": prediction_id,
        "dosha_answers": {
            "body_frame": "medium",
            "hunger": "very_strong",
            "sleep": "sound",
            "feeling": "hot",
            "digestion": "burning",
            "mood": "focused_irritable"
        },
        "skin_type": "combination",
        "age_group": "21-30",
        "season": "summer",
        "lifestyle": ["high_stress"]
    }
    response = client.post(f"{BASE_URL}/plan/generate", json=payload)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 200, f"Failed: {res_data}"
    assert res_data["status"] == "success"
    assert "days" in res_data
    assert len(res_data["days"]) == 7
    # Verify new schema alignments
    assert isinstance(res_data["days"][0]["yoga"], str) # Check that yoga is string (not array)
    assert isinstance(res_data["weekly_summary"]["key_diet_changes"], list) # Check that diet changes is list
    print(f"[OK] Generated 7-day personalized plan successfully.")
    print(f"  Plan Title: {res_data['title']}")
    print(f"  First Day Theme: {res_data['days'][0]['theme']}")
    print(f"  First Day Yoga: {res_data['days'][0]['yoga']}")
    return res_data["id"]

def test_patient_history():
    print("\n[STEP 6] Testing Patient Plan & Scan History Logs...")
    # Plan History
    resp_plan = client.get(f"{BASE_URL}/plan/history")
    print(f"Plan History Status: {resp_plan.status_code}")
    plans = resp_plan.json()
    assert resp_plan.status_code == 200
    assert len(plans) > 0
    
    # Scan History
    resp_scan = client.get(f"{BASE_URL}/predict/history")
    print(f"Scan History Status: {resp_scan.status_code}")
    scans = resp_scan.json()
    assert resp_scan.status_code == 200
    assert scans["status"] == "success"
    assert len(scans["history"]) > 0
    print("[OK] Patient histories checked and validated.")

def test_doctor_vetting(plan_id):
    print("\n[STEP 7] Testing Doctor Vetting, Modifications, and Approvals...")
    # Log in as Doctor
    payload = {
        "email": doctor_email,
        "password": password
    }
    login_resp = client.post(f"{BASE_URL}/auth/login", json=payload)
    assert login_resp.status_code == 200
    doc_token = login_resp.json()["access_token"]
    
    # Authenticate client as Doctor
    client.headers = {"Authorization": f"Bearer {doc_token}"}
    
    # 1. Fetch unchecked plans queue
    queue_resp = client.get(f"{BASE_URL}/plan/unchecked-plans")
    print(f"Doctor Queue Status: {queue_resp.status_code}")
    queue = queue_resp.json()
    assert queue_resp.status_code == 200
    assert len(queue) > 0
    
    # Find our plan in the queue
    found_plan = None
    for p in queue:
        if p["id"] == plan_id:
            found_plan = p
            break
    assert found_plan is not None, "Our generated plan was not in the doctor specialization queue!"
    
    # 2. Modify day 1 theme and submit review
    modified_plan = found_plan.copy()
    modified_plan["days"][0]["theme"] = "Medically Audited Day Focus"
    modified_plan["days"][0]["yoga"] = "Surya Namaskar (Slow)"
    
    review_payload = {
        "is_doctor_vetted": True,
        "doctor_notes": "Added custom Surya Namaskar recommendation for combination skin.",
        "modified_plan": modified_plan
    }
    
    review_resp = client.patch(f"{BASE_URL}/plan/{plan_id}/review", json=review_payload)
    print(f"Doctor Review Submission Status: {review_resp.status_code}")
    review_data = review_resp.json()
    print(f"Review Data: {review_data}")
    assert review_resp.status_code == 200, f"Failed: {review_data}"
    assert review_data["is_doctor_vetted"] is True
    assert review_data["is_doctor_modified"] is True
    assert review_data["days"][0]["theme"] == "Medically Audited Day Focus"
    assert review_data["days"][0]["yoga"] == "Surya Namaskar (Slow)"
    
    # 3. Check reviewed plans list
    rev_list_resp = client.get(f"{BASE_URL}/plan/reviewed-plans")
    reviewed_list = rev_list_resp.json()
    print(f"Reviewed list: {reviewed_list}")
    assert rev_list_resp.status_code == 200, f"Status code: {rev_list_resp.status_code}, data: {reviewed_list}"
    assert any(p["id"] == plan_id for p in reviewed_list), f"Plan ID {plan_id} not found in reviewed list: {reviewed_list}"
    print("[OK] Doctor vetting & plan modification flow works successfully.")

def test_geolocation_shops():
    print("\n[STEP 8] Testing Geolocation OSM Pharmacy Search...")
    # Find shops near Pune coordinates
    payload = {
        "latitude": 18.5204,
        "longitude": 73.8567,
        "radius_km": 5
    }
    response = client.post(f"{BASE_URL}/shops/nearby", json=payload)
    print(f"Status: {response.status_code}")
    res_data = response.json()
    assert response.status_code == 200, f"Failed: {res_data}"
    assert res_data["status"] == "success"
    assert "shops" in res_data
    print(f"[OK] Location matches returned {len(res_data['shops'])} shops.")
    if len(res_data["shops"]) > 0:
        print(f"  First Store: {res_data['shops'][0]['name']} ({res_data['shops'][0]['distance']})")

def test_chatbot_modes(plan_id):
    print("\n[STEP 9] Testing Chatbot (LLM Direct, Non-RAG)...")
    
    # 1. Login as patient again to authenticate as user
    payload = {
        "email": patient_email,
        "password": password
    }
    login_resp = client.post(f"{BASE_URL}/auth/login", json=payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test chatbot response
    print("Sending message: 'What cooling herbs are good for Pitta?'")
    chat_payload = {
        "message": "What cooling herbs are good for Pitta?"
    }
    chat_resp = client.post(f"{BASE_URL}/chat", json=chat_payload)
    print(f"Chat Response Status: {chat_resp.status_code}")
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert "sources" in chat_data
    assert len(chat_data["sources"]) == 0
    print("[OK] Chat response returned answer and empty sources list successfully.")

if __name__ == "__main__":
    try:
        test_patient_registration()
        test_doctor_registration()
        test_patient_login_and_profile()
        pred_id = test_skin_analysis_upload()
        plan_id = test_generate_plan(pred_id)
        test_patient_history()
        test_doctor_vetting(plan_id)
        test_geolocation_shops()
        test_chatbot_modes(plan_id)
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! DB PERSISTENCE IS FULLY VERIFIED.")
        print("="*60 + "\n")
    except AssertionError as e:
        import traceback
        print(f"\n[ERROR] TEST FAILURE: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
