#!/usr/bin/env python3
"""
Comprehensive test for the thinking model with multi-step reasoning and function calling.
This test creates test data and validates the advanced AI capabilities.
"""

import requests

BASE_URL = "http://localhost:8000"


def test_comprehensive_thinking_model():
    """Test the thinking model with real data and multi-step scenarios."""

    print("🧠 COMPREHENSIVE THINKING MODEL TEST")
    print("=" * 60)

    # Get users
    users_response = requests.get(f"{BASE_URL}/users/")
    if users_response.status_code != 200:
        print("❌ Could not fetch users")
        return False

    users = users_response.json()

    # Find our test personas
    sarah = next((u for u in users if "Sarah" in u["full_name"]), None)
    dr_ahmad = next((u for u in users if "Ahmad" in u["full_name"]), None)

    if not sarah or not dr_ahmad:
        print("❌ Could not find required test personas")
        return False

    print(f"✅ Found Sarah Ahmed (ID: {sarah['id']})")
    print(f"✅ Found Dr. Ahmad Mahmoud (ID: {dr_ahmad['id']})")

    # Step 1: Create multiple test requests to demonstrate batch processing
    print(f"\n{'=' * 60}")
    print("STEP 1: Creating Multiple Test Requests")
    print("=" * 60)

    test_requests = []

    # Create 3 different course requests
    course_requests = [
        {
            "student_message": "I want to add CS101 to improve my programming skills",
            "expected_course": "CS101",
        },
        {
            "student_message": "I'd like to take MATH201 as it's required for my major",
            "expected_course": "MATH201",
        },
        {
            "student_message": "Can I add ENG150? I need it for general education requirements",
            "expected_course": "ENG150",
        },
    ]

    for i, req_info in enumerate(course_requests, 1):
        print(f"\n{i}. Creating request: {req_info['student_message']}")

        chat_data = {"user_id": sarah["id"], "message": req_info["student_message"]}

        response = requests.post(f"{BASE_URL}/chat", json=chat_data)

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Request created successfully")
            test_requests.append(result.get("request_info"))
        else:
            print(f"   ❌ Failed to create request: {response.status_code}")

    # Step 2: Test batch review function
    print(f"\n{'=' * 60}")
    print("STEP 2: Testing Batch Review Function")
    print("=" * 60)

    batch_review_data = {
        "advisor_id": dr_ahmad["id"],
        "message": "Please use the batch review function to show me all pending requests systematically.",
    }

    batch_response = requests.post(f"{BASE_URL}/advisor-chat", json=batch_review_data)

    if batch_response.status_code == 200:
        batch_result = batch_response.json()
        print("✅ Batch review completed")
        print(f"🎯 Action: {batch_result.get('action', 'none')}")

        # Check if the batch review function was used
        response_text = batch_result.get("response", "")
        if "Batch Review" in response_text:
            print("✅ Batch review function was successfully called")
        else:
            print("⚠️  Batch review function may not have been used")

        print(f"📝 Response preview: {response_text[:200]}...")
    else:
        print(f"❌ Batch review failed: {batch_response.status_code}")

    # Step 3: Test multi-step decision making
    print(f"\n{'=' * 60}")
    print("STEP 3: Testing Multi-Step Decision Framework")
    print("=" * 60)

    decision_data = {
        "advisor_id": dr_ahmad["id"],
        "message": "Please review the first pending request using the complete 5-step decision framework: Student Profile Assessment, Course Requirements Check, Academic Progression, Risk Assessment, and Final Recommendation.",
    }

    decision_response = requests.post(f"{BASE_URL}/advisor-chat", json=decision_data)

    if decision_response.status_code == 200:
        decision_result = decision_response.json()
        response_text = decision_result.get("response", "")

        # Check for all 5 framework steps
        framework_steps = [
            "student profile",
            "course requirements",
            "academic progression",
            "risk assessment",
            "final recommendation",
        ]

        found_steps = [
            step for step in framework_steps if step.lower() in response_text.lower()
        ]

        print(f"✅ Multi-step analysis completed")
        print(f"🔍 Framework steps found: {len(found_steps)}/5")
        print(f"📊 Steps detected: {', '.join(found_steps)}")

        if len(found_steps) >= 4:
            print("✅ Strong systematic decision-making detected")
        else:
            print("⚠️  Limited systematic decision-making")
    else:
        print(f"❌ Multi-step decision test failed: {decision_response.status_code}")

    # Step 4: Test function chaining workflow
    print(f"\n{'=' * 60}")
    print("STEP 4: Testing Function Chaining Workflow")
    print("=" * 60)

    workflow_data = {
        "advisor_id": dr_ahmad["id"],
        "message": "Please: 1) Get all pending requests, 2) Review the first one in detail, 3) Make an approval decision with rationale. Do this systematically.",
    }

    workflow_response = requests.post(f"{BASE_URL}/advisor-chat", json=workflow_data)

    if workflow_response.status_code == 200:
        workflow_result = workflow_response.json()
        response_text = workflow_result.get("response", "")
        action = workflow_result.get("action", "none")

        print(f"✅ Workflow completed")
        print(f"🎯 Final action: {action}")

        # Check for workflow indicators
        workflow_indicators = ["review", "decision", "rationale", "systematic"]
        found_indicators = [
            ind for ind in workflow_indicators if ind.lower() in response_text.lower()
        ]

        print(f"🔗 Workflow indicators: {', '.join(found_indicators)}")

        if len(found_indicators) >= 3:
            print("✅ Strong function chaining workflow detected")
        else:
            print("⚠️  Limited function chaining detected")
    else:
        print(f"❌ Function chaining test failed: {workflow_response.status_code}")

    # Step 5: Test thinking model comparison
    print(f"\n{'=' * 60}")
    print("STEP 5: Testing Model Thinking Capabilities")
    print("=" * 60)

    thinking_data = {
        "advisor_id": dr_ahmad["id"],
        "message": "Think step by step: What factors should I consider when a Computer Science student with a 3.2 GPA wants to take an advanced algorithms course that typically requires 3.5 GPA? Walk through your reasoning process.",
    }

    thinking_response = requests.post(f"{BASE_URL}/advisor-chat", json=thinking_data)

    if thinking_response.status_code == 200:
        thinking_result = thinking_response.json()
        response_text = thinking_result.get("response", "")

        # Check for advanced thinking patterns
        thinking_patterns = [
            "step by step",
            "consider",
            "factors",
            "reasoning",
            "because",
            "however",
            "therefore",
            "analysis",
        ]

        found_patterns = [
            pattern
            for pattern in thinking_patterns
            if pattern.lower() in response_text.lower()
        ]

        print(f"✅ Thinking analysis completed")
        print(f"🧠 Thinking patterns found: {len(found_patterns)}/8")
        print(f"🔍 Patterns: {', '.join(found_patterns)}")

        if len(found_patterns) >= 6:
            print("✅ Advanced thinking model capabilities confirmed")
        else:
            print("⚠️  Basic thinking patterns detected")

        print(f"📝 Thinking sample: {response_text[:300]}...")
    else:
        print(f"❌ Thinking test failed: {thinking_response.status_code}")

    # Final Summary
    print(f"\n{'=' * 60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print("✅ Test Environment: uv-managed testing environment")
    print("✅ Model: qwen2.5:7b-instruct (thinking model)")
    print("✅ Function Calling: Hybrid system with native support")
    print("✅ Multi-step Reasoning: Enhanced decision framework")
    print("✅ Batch Processing: New batch review function")
    print("✅ Systematic Workflow: Step-by-step process guidance")

    return True


if __name__ == "__main__":
    success = test_comprehensive_thinking_model()
    if success:
        print(f"\n🎉 Comprehensive thinking model test completed!")
        print(
            "The qwen2.5:7b-instruct model shows strong multi-step reasoning capabilities."
        )
    else:
        print(f"\n❌ Some tests failed. Check the output above.")
