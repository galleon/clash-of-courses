#!/usr/bin/env python3
"""Test room name display in student schedule"""

import requests
import json

# Test the current schedule functionality to see if room names display correctly
url = "http://localhost:8000/api/chat/student"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6OTk5OTk5OTk5OX0.Hmiqi5Wuhw_5YseW1bXWs4iZ5xtOVgMmEKBuSE5g3bg"
}

# Get current schedule
payload = {
    "message": "What is my current schedule?",
    "conversation_id": "test_room_display"
}

print("Testing room name display in schedule...")
print("=" * 50)

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check if the response contains room names instead of UUIDs
        if 'response' in result:
            response_text = result['response']
            if 'Einstein' in response_text or 'Curie' in response_text or 'Newton' in response_text:
                print("\n✅ SUCCESS: Room names are displaying correctly!")
            elif any(len(word) == 36 and '-' in word for word in response_text.split()):
                print("\n❌ ISSUE: Still showing UUIDs instead of room names")
            else:
                print("\n⚠️  UNCLEAR: Response doesn't clearly show room information")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error testing: {e}")