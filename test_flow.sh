#!/bin/bash
BASE_URL="http://127.0.0.1:8000"
EMAIL="test_$RANDOM@example.com"
echo "Registering user: $EMAIL"
curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\", \"password\":\"password\", \"username\":\"test\"}" > /dev/null
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" -d "username=$EMAIL&password=password" | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')
echo "Token: $TOKEN"

echo "Completing onboarding (should generate templates)..."
curl -s -X PUT "$BASE_URL/users/me/profile" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"goals":"Study","focus_times":"Morning", "onboarding_completed":true}' > /dev/null

echo "Fetching templates..."
TEMPLATES=$(curl -s -X GET "$BASE_URL/templates" -H "Authorization: Bearer $TOKEN")
echo "$TEMPLATES" | grep -o '"name":"[^"]*"'

# Get first template id
TEMPLATE_ID=$(echo "$TEMPLATES" | grep -o '"id":"[^"]*' | head -n 1 | grep -o '[^"]*$')
echo "Selected Template: $TEMPLATE_ID"

echo "Applying template..."
curl -s -X PUT "$BASE_URL/users/me/profile" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"active_planner_id\":\"$TEMPLATE_ID\"}" > /dev/null

echo "Getting profile to trigger daily reset..."
curl -s -X GET "$BASE_URL/users/me/profile" -H "Authorization: Bearer $TOKEN" > /dev/null

echo "Fetching tasks for today..."
curl -s -X GET "$BASE_URL/tasks" -H "Authorization: Bearer $TOKEN" | grep -o '"title":"[^"]*"'
