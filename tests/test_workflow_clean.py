#!/usr/bin/env python3
"""
BRS Prototype Workflow Test Script

This script tests the complete advisor approval workflow:
1. Reset database to fresh state
2. Sarah checks updates (should be none)
3. Sarah requests CS101 (should get "sent to advisor" response)
4. Dr. Ahmad checks requests (should have one request)
5. Dr. Ahmad reviews request details (should show Sarah's request)
6. Dr. Ahmad approves the request (should confirm approval)

Each step must pass or the test fails immediately.

Usage: python3 test_workflow.py
"""

import requests
import time
import subprocess
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/chat"
ADVISOR_CHAT_ENDPOINT = f"{BASE_URL}/advisor-chat"
USERS_ENDPOINT = f"{BASE_URL}/users/"
REQUESTS_ENDPOINT = f"{BASE_URL}/requests/"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n[STEP {step_num}] {description}")
    print("-" * 50)


def assert_test(condition, message):
    """Assert a test condition, exit immediately if false"""
    if condition:
        print(f"✅ {message}")
    else:
        print(f"❌ FAILED: {message}")
        sys.exit(1)


def send_chat_message(user_id, message, endpoint=CHAT_ENDPOINT):
    """Send a chat message and return the response"""
    if endpoint == CHAT_ENDPOINT:
        payload = {"student_id": user_id, "message": message}
    else:
        payload = {"advisor_id": user_id, "message": message}

    print(f"🤖 Sending: '{message}'")

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        ai_response = result.get("response", "No response received")
        print(f"🤖 AI Response: {ai_response}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending chat message: {e}")
        return None


def get_user_by_username(username):
    """Get user information by username"""
    try:
        response = requests.get(USERS_ENDPOINT)
        response.raise_for_status()
        users = response.json()

        for user in users:
            if user["username"] == username:
                return user
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching users: {e}")
        return None


def reset_database():
    """Reset the database to fresh state with seed data"""
    print("🔄 Resetting database to fresh state...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "backend",
                "python",
                "/app/seed_personas.py",
            ],
            capture_output=True,
            text=True,
            cwd="../",
        )

        if result.returncode == 0:
            print("✅ Database reset successfully")
            return True
        else:
            print(f"❌ Database reset failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Database reset error: {e}")
        return False


def verify_database_state():
    """Verify the database has been properly reset"""
    try:
        # Check requests count (should be 0)
        req_response = requests.get(REQUESTS_ENDPOINT)
        req_response.raise_for_status()
        requests_count = len(req_response.json())

        # Check users count (should be 7)
        users_response = requests.get(USERS_ENDPOINT)
        users_response.raise_for_status()
        users_count = len(users_response.json())

        print(f"📊 Database State: {requests_count} requests, {users_count} users")
        return requests_count == 0 and users_count == 7
    except Exception as e:
        print(f"❌ Database verification error: {e}")
        return False


def check_semantic_similarity(response_text, expected_meaning):
    """Use Ollama to check semantic similarity"""
    prompt = f"""You are a precise semantic similarity checker for a course registration system.

RESPONSE TEXT: "{response_text[:500]}"
EXPECTED MEANING: "{expected_meaning}"

Task: Determine if the response text conveys the same core meaning as the expected meaning.

Rules:
- Focus on the main message, not exact wording
- Consider the context of course registration
- Ignore formatting, length differences, and additional details
- Only care if the CORE MESSAGE is the same

Reply with EXACTLY one character:
1 = Core meanings are the same
0 = Core meanings are different

Your answer (only 1 or 0):"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:27b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9, "max_tokens": 10},
            },
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "0").strip()
            first_char = answer[0] if answer else "0"
            similarity_score = 1 if first_char == "1" else 0
            print(f"   🤖 Semantic check: {similarity_score} (raw: '{answer[:10]}...')")
            return similarity_score == 1
        else:
            print(f"⚠️ Ollama API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Semantic similarity check failed: {e}")
        return False


def get_requests_count():
    """Get current number of requests"""
    try:
        response = requests.get(REQUESTS_ENDPOINT)
        response.raise_for_status()
        return len(response.json())
    except Exception as e:
        print(f"❌ Error getting requests count: {e}")
        return -1


def main():
    """Main test workflow - stops on first failure"""
    print_section("BRS PROTOTYPE WORKFLOW TEST")
    print(f"Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # =================================================================
    # STEP 1: Reset database to fresh state
    # =================================================================
    print_step(1, "Reset database to fresh state")
    assert_test(reset_database(), "Database reset completed")
    time.sleep(3)
    assert_test(verify_database_state(), "Database verified (0 requests, 7 users)")

    # Get user information
    sarah = get_user_by_username("sarah.ahmed")
    dr_ahmad = get_user_by_username("dr.ahmad")
    assert_test(sarah is not None, f"Found Sarah Ahmed (ID: {sarah['id']})")
    assert_test(dr_ahmad is not None, f"Found Dr. Ahmad Mahmoud (ID: {dr_ahmad['id']})")

    # =================================================================
    # STEP 2: Sarah checks for updates (should be none)
    # =================================================================
    print_step(2, "Sarah checks for updates (should be none)")
    sarah_response1 = send_chat_message(
        sarah["id"], "Hello! Have there been any updates to my account?"
    )
    assert_test(sarah_response1 is not None, "Sarah successfully checked for updates")

    updates_response = sarah_response1.get("response", "")
    no_updates = check_semantic_similarity(
        updates_response, "No recent updates or requests found"
    )
    assert_test(no_updates, "Sarah correctly sees no pending requests initially")

    time.sleep(2)

    # =================================================================
    # STEP 3: Sarah requests CS101 (should get advisor approval message)
    # =================================================================
    print_step(3, "Sarah requests CS101 (should get advisor approval message)")
    sarah_response2 = send_chat_message(
        sarah["id"],
        "I would like to request enrollment in CS101 - Introduction to Computer Science.",
    )
    assert_test(sarah_response2 is not None, "Sarah's CS101 request was processed")

    enrollment_response = sarah_response2.get("response", "")
    approval_message = check_semantic_similarity(
        enrollment_response, "Your request has been sent to an advisor for approval"
    )
    assert_test(approval_message, "Sarah gets correct 'sent to advisor' response")

    # Verify request was created
    assert_test(get_requests_count() == 1, "One request created in database")
    time.sleep(2)

    # =================================================================
    # STEP 4: Dr. Ahmad checks for requests (should have one)
    # =================================================================
    print_step(4, "Dr. Ahmad checks for requests (should have one)")
    ahmad_response1 = send_chat_message(
        dr_ahmad["id"],
        "Hello! Do I have any requests to review?",
        ADVISOR_CHAT_ENDPOINT,
    )
    assert_test(
        ahmad_response1 is not None, "Dr. Ahmad successfully checked for requests"
    )

    requests_response = ahmad_response1.get("response", "")
    has_requests = check_semantic_similarity(
        requests_response, "You have one pending request to review"
    )
    assert_test(has_requests, "Dr. Ahmad sees one pending request")

    time.sleep(2)

    # =================================================================
    # STEP 5: Dr. Ahmad reviews request details
    # =================================================================
    print_step(5, "Dr. Ahmad reviews request details")
    ahmad_response2 = send_chat_message(
        dr_ahmad["id"],
        "Please show me the details of the pending request",
        ADVISOR_CHAT_ENDPOINT,
    )
    assert_test(ahmad_response2 is not None, "Dr. Ahmad got request details")

    details_response = ahmad_response2.get("response", "")
    has_details = check_semantic_similarity(
        details_response,
        "Sarah Ahmed wants to add CS101 Introduction to Computer Science",
    )
    assert_test(has_details, "Dr. Ahmad sees Sarah's CS101 request details")

    time.sleep(2)

    # =================================================================
    # STEP 6: Dr. Ahmad approves the request
    # =================================================================
    print_step(6, "Dr. Ahmad approves the request")
    ahmad_response3 = send_chat_message(
        dr_ahmad["id"],
        "I approve Sarah's request for CS101. She has valid academic reasons.",
        ADVISOR_CHAT_ENDPOINT,
    )
    assert_test(ahmad_response3 is not None, "Dr. Ahmad's approval was processed")

    approval_response = ahmad_response3.get("response", "")
    approval_confirmed = check_semantic_similarity(
        approval_response, "Request has been approved successfully"
    )
    assert_test(approval_confirmed, "Dr. Ahmad gets approval confirmation")

    time.sleep(3)  # Wait for database update

    # Verify approval was saved to database
    try:
        response = requests.get(REQUESTS_ENDPOINT)
        response.raise_for_status()
        requests_data = response.json()
        approved_requests = [r for r in requests_data if r.get("status") == "approved"]
        assert_test(
            len(approved_requests) == 1,
            "Request status updated to 'approved' in database",
        )
    except Exception as e:
        assert_test(False, f"Failed to verify database approval: {e}")

    # =================================================================
    # SUCCESS!
    # =================================================================
    print_section("TEST COMPLETED SUCCESSFULLY")
    print("🎉 All workflow steps passed!")
    print("✅ Database reset working")
    print("✅ Student request creation working")
    print("✅ Advisor request review working")
    print("✅ Advisor approval working")
    print("✅ Database persistence working")
    print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
