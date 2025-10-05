"""Test the LangGraph student agent implementation."""

import os
import sys
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, "/Users/alleon_g/code/brs_prototype/backend")

from brs_backend.agents.student_agent_langgraph import process_student_request


async def test_student_agent():
    """Test the student agent with a simple request."""

    print("🧪 Testing LangGraph Student Agent")
    print("=" * 50)

    # Test 1: Get current schedule
    print("\n📅 Test 1: Get current schedule")
    try:
        response = process_student_request(
            message="What's my current schedule?",
            student_id="1",  # Use student ID 1 from our test data
            conversation_history=[],
        )
        print(f"✅ Response: {response['response'][:200]}...")
        print(f"📊 Metadata: {response['metadata']}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Search for courses
    print("\n🔍 Test 2: Search for courses")
    try:
        response = process_student_request(
            message="What computer science courses are available?",
            student_id="1",
            conversation_history=[],
        )
        print(f"✅ Response: {response['response'][:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Check course attachability
    print("\n✅ Test 3: Check course eligibility")
    try:
        response = process_student_request(
            message="Can I enroll in CS102?", student_id="1", conversation_history=[]
        )
        print(f"✅ Response: {response['response'][:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🏁 LangGraph Student Agent Test Complete")


if __name__ == "__main__":
    # Set environment variables if needed
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://brs_user:brs_password@localhost:5432/brs_db"
    )
    os.environ.setdefault("OPENAI_API_KEY", "your-openai-api-key-here")

    # Run the test
    asyncio.run(test_student_agent())
