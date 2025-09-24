#!/usr/bin/env python3
"""Quick test for approval functionality only."""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
ADVISOR_CHAT_ENDPOINT = f"{BACKEND_URL}/advisor-chat"
REQUESTS_ENDPOINT = f"{BACKEND_URL}/requests"


def send_chat_message(user_id, message, endpoint, conversation_context=""):
    """Send a chat message and return the response."""
    if "advisor-chat" in endpoint:
        payload = {
            "advisor_id": user_id,
            "message": message,
            "conversation_history": [{"type": "user", "content": conversation_context}]
            if conversation_context
            else [],
        }
    else:
        payload = {
            "user_id": user_id,
            "message": message,
            "conversation_history": [{"type": "user", "content": conversation_context}]
            if conversation_context
            else [],
        }

    print(f"🤖 Sending: '{message}'")
    if conversation_context:
        print(f"📝 Context: {conversation_context[:100]}...")

    response = requests.post(endpoint, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 AI Response: {data.get('response', 'No response')[:200]}...")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


def main():
    print("=" * 60)
    print(" TESTING APPROVAL FUNCTIONALITY ONLY")
    print("=" * 60)

    # Get users
    users_response = requests.get(f"{BACKEND_URL}/users/")
    users = users_response.json()

    dr_ahmad = next((u for u in users if "Ahmad" in u["full_name"]), None)

    if not dr_ahmad:
        print("❌ Could not find Dr. Ahmad")
        return

    print(f"✅ Found Dr. Ahmad Mahmoud (ID: {dr_ahmad['id']})")

    # Get current requests
    requests_response = requests.get(REQUESTS_ENDPOINT)
    current_requests = requests_response.json()

    if not current_requests:
        print("❌ No requests found to test approval")
        return

    test_request = current_requests[0]
    print(
        f"📝 Testing with Request #{test_request['id']}: Student ID {test_request['student_id']} - Course ID {test_request['course_id']}"
    )

    # Step 1: Review the request first
    print("\n[STEP 1] Dr. Ahmad reviews the request")
    print("-" * 40)

    review_response = send_chat_message(
        dr_ahmad["id"],
        f"Please show me the details for request #{test_request['id']}.",
        ADVISOR_CHAT_ENDPOINT,
    )

    if not review_response:
        print("❌ Review request failed")
        return

    time.sleep(2)

    # Step 2: Approve the request
    print("\n[STEP 2] Dr. Ahmad approves the request")
    print("-" * 40)

    approval_context = f"I just reviewed request #{test_request['id']} for student ID {test_request['student_id']}"

    approval_response = send_chat_message(
        dr_ahmad["id"],
        "I approve this request. The student has valid academic reasons.",
        ADVISOR_CHAT_ENDPOINT,
        conversation_context=approval_context,
    )

    if not approval_response:
        print("❌ Approval request failed")
        return

    # Step 3: Check if it was actually approved
    print("\n[STEP 3] Verifying approval in database")
    print("-" * 40)

    time.sleep(2)  # Wait for database update
    updated_requests = requests.get(REQUESTS_ENDPOINT).json()
    updated_request = next(
        (r for r in updated_requests if r["id"] == test_request["id"]), None
    )

    if not updated_request:
        print("❌ Request not found after approval")
        return

    print(f"📊 Request status: {updated_request['status']}")
    print(f"📊 Advisor ID: {updated_request.get('advisor_id', 'None')}")

    if updated_request["status"] == "approved":
        print("✅ SUCCESS: Request was properly approved!")
    else:
        print(
            f"❌ FAILED: Request status is '{updated_request['status']}' instead of 'approved'"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
