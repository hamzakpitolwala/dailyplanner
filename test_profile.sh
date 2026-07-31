#!/bin/bash
BASE_URL="http://127.0.0.1:8000"
EMAIL="test_$RANDOM@example.com"
curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\", \"password\":\"password\", \"username\":\"test\"}" > /dev/null
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" -d "username=$EMAIL&password=password" | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')
echo "Token: $TOKEN"

echo "GET Profile:"
curl -s -X GET "$BASE_URL/users/me/profile" -H "Authorization: Bearer $TOKEN"

echo -e "\nPUT Profile:"
curl -s -X PUT "$BASE_URL/users/me/profile" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"goals":"Study","onboarding_completed":true}'
