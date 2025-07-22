# Complete API Testing Guide

This guide provides comprehensive testing procedures for the deployed FastAPI backend on AWS App Runner.

## Prerequisites

- Deployed App Runner service (see MANUAL-DEPLOYMENT-GUIDE.md)
- `curl` and `jq` installed for API testing
- Your App Runner URL and API key ready

```bash
# Set your deployment variables
export APP_RUNNER_URL="https://your-unique-id.us-east-1.awsapprunner.com"
export API_KEY="your-super-secure-api-key-12345"
```

## Test Suite 1: Basic Connectivity

### 1.1 Health Check (No Auth Required)

```bash
echo "=== Testing Health Endpoint ==="
curl -i "$APP_RUNNER_URL/health"
```

**Expected Response:**
- Status: `200 OK`
- Body: `{"success": true, "status": "healthy", "components": {...}}`

### 1.2 Root Endpoint (No Auth Required)

```bash
echo "=== Testing Root Endpoint ==="
curl -i "$APP_RUNNER_URL/"
```

**Expected Response:**
- Status: `200 OK`
- Body: API information with version and timestamp

### 1.3 Authentication Test

```bash
echo "=== Testing Authentication ==="
# Should fail without API key
curl -i "$APP_RUNNER_URL/users"

echo ""
echo "=== Testing with API Key ==="
# Should succeed with API key
curl -i -H "Authorization: Bearer $API_KEY" "$APP_RUNNER_URL/users"
```

**Expected Responses:**
- Without API key: `403 Forbidden` or `401 Unauthorized`
- With API key: `200 OK` with user list (likely empty)

## Test Suite 2: User Management API

### 2.1 Create User (Level 1 Fields Only)

```bash
echo "=== Creating User (Level 1 Fields) ==="
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Johnson"
  }' \
  "$APP_RUNNER_URL/users")

echo "$RESPONSE" | jq

# Extract user ID for subsequent tests
USER_ID_1=$(echo "$RESPONSE" | jq -r '.data.user_id')
echo "Created user ID: $USER_ID_1"
```

### 2.2 Create User (All PII Levels)

```bash
echo "=== Creating User (All PII Levels) ==="
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "first_name": "Bob",
    "last_name": "Smith",
    "phone": "+1-555-0123",
    "address": "123 Main Street, Anytown, USA 12345",
    "date_of_birth": "1985-03-15",
    "ip_address": "192.168.1.100",
    "ssn": "123-45-6789",
    "bank_account": "1234567890",
    "credit_card": "4111-1111-1111-1111"
  }' \
  "$APP_RUNNER_URL/users")

echo "$RESPONSE" | jq

USER_ID_2=$(echo "$RESPONSE" | jq -r '.data.user_id')
echo "Created user ID: $USER_ID_2"
```

### 2.3 Get User by ID

```bash
echo "=== Getting User by ID ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/$USER_ID_2" | jq
```

**Verify:**
- All fields are present
- Level 1 fields (email, names) are readable
- Level 2/3 fields should be decrypted and displayed

### 2.4 List Users

```bash
echo "=== Listing Users ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?limit=10" | jq
```

**Verify:**
- Returns array of users
- Pagination info (total, limit, offset)
- Only basic fields shown in list view

### 2.5 Test Pagination

```bash
echo "=== Testing Pagination ==="
# Test with different limits
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?limit=1&offset=0" | jq

curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?limit=1&offset=1" | jq
```

### 2.6 Test Input Validation

```bash
echo "=== Testing Input Validation ==="

# Invalid email
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "first_name": "Test", "last_name": "User"}' \
  "$APP_RUNNER_URL/users" | jq

# Invalid SSN format
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "first_name": "Test", "last_name": "User", "ssn": "invalid"}' \
  "$APP_RUNNER_URL/users" | jq

# Invalid date format
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "first_name": "Test", "last_name": "User", "date_of_birth": "invalid-date"}' \
  "$APP_RUNNER_URL/users" | jq
```

**Expected:** All should return `400 Bad Request` with validation errors

## Test Suite 3: Audit Trail API

### 3.1 Get User Audit Trail

```bash
echo "=== Getting User Audit Trail ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/$USER_ID_2/audit?limit=10" | jq
```

**Verify:**
- Shows `create_user` operation
- Contains operation details
- No sensitive data in logs

### 3.2 Get System-wide Audit Trail

```bash
echo "=== Getting System Audit Trail ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/audit?limit=20" | jq
```

**Verify:**
- Shows all operations from testing
- Multiple users' operations visible
- Proper audit metadata

## Test Suite 4: Edge Cases and Error Handling

### 4.1 Test Non-existent User

```bash
echo "=== Testing Non-existent User ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/00000000-0000-0000-0000-000000000000" | jq
```

**Expected:** `404 Not Found`

### 4.2 Test Invalid UUID Format

```bash
echo "=== Testing Invalid UUID ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/invalid-uuid" | jq
```

**Expected:** `400 Bad Request`

### 4.3 Test Invalid Pagination Parameters

```bash
echo "=== Testing Invalid Pagination ==="
# Negative offset
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?offset=-1" | jq

# Zero limit
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?limit=0" | jq

# Excessive limit
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users?limit=1000" | jq
```

**Expected:** All should return `400 Bad Request`

### 4.4 Test Wrong HTTP Methods

```bash
echo "=== Testing Wrong HTTP Methods ==="
# POST to get user (should be GET)
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/$USER_ID_1" | jq
```

**Expected:** `405 Method Not Allowed`

## Test Suite 5: Security Tests

### 5.1 Test Missing Authentication

```bash
echo "=== Testing Missing Authentication ==="
curl -s "$APP_RUNNER_URL/users" | jq
```

### 5.2 Test Invalid API Key

```bash
echo "=== Testing Invalid API Key ==="
curl -s -H "Authorization: Bearer invalid-key" \
  "$APP_RUNNER_URL/users" | jq
```

### 5.3 Test Malformed Authorization Header

```bash
echo "=== Testing Malformed Auth Header ==="
curl -s -H "Authorization: invalid-format" \
  "$APP_RUNNER_URL/users" | jq
```

**Expected:** All should return `401 Unauthorized` or `403 Forbidden`

## Test Suite 6: Performance Tests

### 6.1 Response Time Test

```bash
echo "=== Testing Response Times ==="
# Test multiple requests and measure time
for i in {1..5}; do
  echo "Request $i:"
  time curl -s -H "Authorization: Bearer $API_KEY" \
    "$APP_RUNNER_URL/health" > /dev/null
done
```

### 6.2 Concurrent Requests Test

```bash
echo "=== Testing Concurrent Requests ==="
# Run 5 requests in parallel
for i in {1..5}; do
  curl -s -H "Authorization: Bearer $API_KEY" \
    "$APP_RUNNER_URL/users" | jq -c '.success' &
done
wait
```

## Test Suite 7: Data Encryption Verification

### 7.1 Verify Different PII Levels Work

```bash
echo "=== Creating Users with Different PII Levels ==="

# Level 1 only (RDS encryption)
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "level1@example.com", "first_name": "Level1", "last_name": "User"}' \
  "$APP_RUNNER_URL/users" | jq '.data.user_id'

# Level 2 (KMS encryption)
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "level2@example.com", "first_name": "Level2", "last_name": "User", "address": "123 Secret Ave"}' \
  "$APP_RUNNER_URL/users" | jq '.data.user_id'

# Level 3 (Double encryption)
curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "level3@example.com", "first_name": "Level3", "last_name": "User", "ssn": "555-55-5555"}' \
  "$APP_RUNNER_URL/users" | jq '.data.user_id'
```

## Test Suite 8: Cleanup Test

### 8.1 Delete Users

```bash
echo "=== Testing User Deletion ==="
if [ ! -z "$USER_ID_1" ]; then
  curl -s -X DELETE -H "Authorization: Bearer $API_KEY" \
    "$APP_RUNNER_URL/users/$USER_ID_1" | jq
fi

if [ ! -z "$USER_ID_2" ]; then
  curl -s -X DELETE -H "Authorization: Bearer $API_KEY" \
    "$APP_RUNNER_URL/users/$USER_ID_2" | jq
fi
```

### 8.2 Verify Deletion

```bash
echo "=== Verifying Deletion ==="
curl -s -H "Authorization: Bearer $API_KEY" \
  "$APP_RUNNER_URL/users/$USER_ID_1" | jq

# Should return 404 Not Found
```

## Complete Test Script

Here's a complete test script that runs all tests:

```bash
#!/bin/bash
# complete-api-test.sh

# Configuration
APP_RUNNER_URL="https://your-unique-id.us-east-1.awsapprunner.com"
API_KEY="your-super-secure-api-key-12345"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
passed_count=0

function run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    
    echo -e "${YELLOW}Testing: $test_name${NC}"
    
    response=$(eval "$command" 2>/dev/null)
    status=$?
    
    ((test_count++))
    
    if [ $status -eq $expected_status ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((passed_count++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Expected status: $expected_status, Got: $status"
    fi
    echo ""
}

# Run tests
echo "Starting comprehensive API tests..."
echo "App Runner URL: $APP_RUNNER_URL"
echo ""

# Basic connectivity
run_test "Health Check" "curl -s $APP_RUNNER_URL/health | jq -e '.success == true'" 0
run_test "Root Endpoint" "curl -s $APP_RUNNER_URL/ | jq -e '.success == true'" 0

# Authentication
run_test "No Auth (should fail)" "curl -s $APP_RUNNER_URL/users | jq -e '.success == true'" 1
run_test "Valid Auth" "curl -s -H 'Authorization: Bearer $API_KEY' $APP_RUNNER_URL/users | jq -e '.success == true'" 0

# User operations
run_test "Create User" "curl -s -X POST -H 'Authorization: Bearer $API_KEY' -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"first_name\":\"Test\",\"last_name\":\"User\"}' $APP_RUNNER_URL/users | jq -e '.success == true'" 0

echo ""
echo "Test Results: $passed_count/$test_count tests passed"

if [ $passed_count -eq $test_count ]; then
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check the deployment.${NC}"
    exit 1
fi
```

## Expected Results Summary

✅ **Successful deployment indicators:**
- Health endpoint returns healthy status
- All CRUD operations work
- Authentication properly blocks unauthorized requests
- Input validation catches invalid data
- Audit trail records all operations
- Response times under 2 seconds (after warmup)
- No errors in CloudWatch logs

❌ **Common issues:**
- Lambda invocation failures (check IAM permissions)
- Database connection errors (check Lambda VPC configuration)
- Authentication failures (check API key configuration)
- Validation errors (check request format)

Use this guide to systematically verify your deployment works correctly before connecting a frontend!