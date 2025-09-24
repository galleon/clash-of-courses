#!/usr/bin/env python3
"""
Test to validate the improved client-side status tracking.
"""

import requests
import time

BASE_URL = "http://localhost:8000"


def test_client_side_improvements():
    print("🧪 Testing Client-Side Improvements")
    print("=" * 50)

    # Create a test request to see if the frontend picks it up
    users_response = requests.get(f"{BASE_URL}/users/")
    users = users_response.json()

    sarah = next((u for u in users if "Sarah" in u["full_name"]), None)

    if not sarah:
        print("❌ Could not find Sarah")
        return

    print(f"✅ Found Sarah (ID: {sarah['id']})")

    # Create a new test request directly via API
    new_request = {
        "student_id": sarah["id"],
        "course_id": 129,  # CS101
        "request_type": "add",
        "justification": "Testing client-side refresh functionality",
    }

    response = requests.post(f"{BASE_URL}/requests/", json=new_request)

    if response.status_code in [200, 201]:
        request_data = response.json()
        request_id = request_data["id"]
        print(f"✅ Created test request #{request_id}")
    else:
        print(f"❌ Failed to create request: {response.status_code}")
        return

    print("\n🎯 Now test the frontend improvements:")
    print("1. Go to http://localhost:3000")
    print("2. Log in as Sarah Ahmed")
    print("3. You should see the new request status in the blue status bar")
    print("4. Click the '🔄 Refresh' button to manually refresh")
    print("5. The status should update automatically every 30 seconds")
    print("6. When you ask about request status, it should refresh automatically")

    print(f"\n📊 Current request #{request_id} status: pending")
    print("Now approve it via Dr. Ahmad to test the refresh...")


if __name__ == "__main__":
    test_client_side_improvements()
