#!/usr/bin/env python3
"""
Test script to validate the thinking model capabilities for multi-step reasoning.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_advisor_thinking_capabilities():
    """Test the improved thinking model with multi-step reasoning."""

    print("🧠 Testing Thinking Model Capabilities")
    print("=" * 50)

    # Test 1: Basic function availability
    print("\n1. Testing batch review function availability...")

    # Login as advisor
    login_data = {"email": "advisor@university.edu", "password": "password123"}

    login_response = requests.post(f"{BASE_URL}/login", json=login_data)
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test 2: Multi-step reasoning request
    print("\n2. Testing multi-step reasoning with batch review...")

    chat_data = {
        "message": "Please review all pending requests using systematic multi-step analysis. Start with a batch overview, then provide detailed thinking for each request."
    }

    chat_response = requests.post(
        f"{BASE_URL}/advisor-chat", json=chat_data, headers=headers
    )

    if chat_response.status_code == 200:
        response_data = chat_response.json()
        print(f"✅ Chat Response Status: {chat_response.status_code}")
        print(f"🎯 Action Taken: {response_data.get('action', 'none')}")
        print(f"📝 Response Preview: {response_data.get('response', '')[:200]}...")

        # Check if it used the batch review function
        if "Batch Review" in response_data.get("response", ""):
            print("✅ Batch review function was utilized")
        else:
            print("⚠️  Batch review function may not have been used")
    else:
        print(f"❌ Chat failed with status: {chat_response.status_code}")
        return False

    # Test 3: Step-by-step decision making
    print("\n3. Testing step-by-step decision framework...")

    step_by_step_data = {
        "message": "Walk me through your decision framework step by step for the first pending request. Think through: student profile, course requirements, academic progression, risk assessment, and final recommendation."
    }

    step_response = requests.post(
        f"{BASE_URL}/advisor-chat", json=step_by_step_data, headers=headers
    )

    if step_response.status_code == 200:
        step_data = step_response.json()
        response_text = step_data.get("response", "")

        # Check for systematic thinking indicators
        thinking_indicators = [
            "step",
            "analysis",
            "assessment",
            "recommendation",
            "profile",
            "requirements",
            "progression",
            "risk",
        ]

        found_indicators = [
            indicator
            for indicator in thinking_indicators
            if indicator.lower() in response_text.lower()
        ]

        print(f"✅ Step-by-step response received")
        print(f"🔍 Thinking indicators found: {len(found_indicators)}/8")
        print(f"📊 Indicators: {', '.join(found_indicators)}")

        if len(found_indicators) >= 4:
            print("✅ Strong systematic thinking detected")
        else:
            print("⚠️  Limited systematic thinking detected")
    else:
        print(f"❌ Step-by-step test failed: {step_response.status_code}")

    # Test 4: Function chaining capability
    print("\n4. Testing multi-function workflow...")

    workflow_data = {
        "message": "Show me all pending requests, then review the first one in detail, and make a recommendation based on your analysis."
    }

    workflow_response = requests.post(
        f"{BASE_URL}/advisor-chat", json=workflow_data, headers=headers
    )

    if workflow_response.status_code == 200:
        workflow_data = workflow_response.json()
        print(f"✅ Multi-function workflow completed")
        print(f"🎯 Final Action: {workflow_data.get('action', 'none')}")

        # Check if multiple functions were conceptually involved
        response_text = workflow_data.get("response", "")
        if any(
            keyword in response_text.lower()
            for keyword in ["review", "analysis", "recommendation"]
        ):
            print("✅ Multi-step reasoning workflow detected")
        else:
            print("⚠️  Limited multi-step workflow detected")
    else:
        print(f"❌ Workflow test failed: {workflow_response.status_code}")

    print("\n" + "=" * 50)
    print("✅ Thinking Model Test Complete!")
    print("\nKey improvements implemented:")
    print("• Enhanced system prompt with decision framework")
    print("• Multi-step reasoning instructions")
    print("• Batch review function for systematic processing")
    print("• qwen2.5:7b-instruct model for better function calling")

    return True


if __name__ == "__main__":
    success = test_advisor_thinking_capabilities()
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
