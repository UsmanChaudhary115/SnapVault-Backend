# 📮 SnapVault Backend - Postman Test Cases

This document provides comprehensive test cases for all API endpoints that you can use in Postman.

## 🚀 Setup Instructions

### 1. Base Configuration
- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json` (for most requests)
- **Authorization**: `Bearer {{token}}` (for protected endpoints)

### 2. Environment Variables (Recommended)
Create these variables in Postman:
- `base_url`: `http://localhost:8000`
- `token`: (will be set after login)
- `user_email`: `test@example.com`
- `user_password`: `testpassword123`
- `group_id`: (will be set after group creation)
- `photo_id`: (will be set after photo upload)

---

## 🔐 Authentication Endpoints

### 1. Register User

#### Test Case 1.1: Successful Registration
```http
POST {{base_url}}/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```
**Expected Response**: `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "bio": "",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Test Case 1.2: Registration with Existing Email
```http
POST {{base_url}}/auth/register
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "john.doe@example.com",
  "password": "anotherpassword123"
}
```
**Expected Response**: `400 Bad Request`
```json
{
  "detail": "Email already exists"
}
```

#### Test Case 1.3: Registration with Invalid Data
```http
POST {{base_url}}/auth/register
Content-Type: application/json

{
  "name": "",
  "email": "invalid-email",
  "password": "123"
}
```
**Expected Response**: `422 Unprocessable Entity`

#### Test Case 1.4: Registration with Missing Fields
```http
POST {{base_url}}/auth/register
Content-Type: application/json

{
  "name": "Test User"
}
```
**Expected Response**: `422 Unprocessable Entity`

### 2. Login User

#### Test Case 2.1: Successful Login
```http
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```
**Expected Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
**Postman Test Script**:
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access_token');
    pm.environment.set("token", jsonData.access_token);
});
```

#### Test Case 2.2: Login with Wrong Password
```http
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "wrongpassword"
}
```
**Expected Response**: `401 Unauthorized`
```json
{
  "detail": "Invalid credentials"
}
```

#### Test Case 2.3: Login with Non-existent Email
```http
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "email": "nonexistent@example.com",
  "password": "somepassword"
}
```
**Expected Response**: `401 Unauthorized`

### 3. Get Current User

#### Test Case 3.1: Get User Info (Authenticated)
```http
GET {{base_url}}/auth/me
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "bio": "",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Test Case 3.2: Get User Info (No Token)
```http
GET {{base_url}}/auth/me
```
**Expected Response**: `401 Unauthorized`

#### Test Case 3.3: Get User Info (Invalid Token)
```http
GET {{base_url}}/auth/me
Authorization: Bearer invalid_token_here
```
**Expected Response**: `401 Unauthorized`

### 4. Update Bio

#### Test Case 4.1: Update Bio Successfully
```http
PUT {{base_url}}/auth/bio/This is my new bio
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "bio": "This is my new bio",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Test Case 4.2: Update Bio with Special Characters
```http
PUT {{base_url}}/auth/bio/Hello! I'm a developer & photographer 🚀
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`

#### Test Case 4.3: Update Bio (Unauthorized)
```http
PUT {{base_url}}/auth/bio/Unauthorized bio update
```
**Expected Response**: `401 Unauthorized`

### 5. Update Password

#### Test Case 5.1: Successful Password Update
```http
PUT {{base_url}}/auth/update-password
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "current_password": "securepassword123",
  "new_password": "newsecurepassword456"
}
```
**Expected Response**: `200 OK`
```json
{
  "message": "Password updated successfully"
}
```

#### Test Case 5.2: Wrong Current Password
```http
PUT {{base_url}}/auth/update-password
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "current_password": "wrongpassword",
  "new_password": "newsecurepassword456"
}
```
**Expected Response**: `400 Bad Request`
```json
{
  "detail": "Current password is incorrect"
}
```

#### Test Case 5.3: Same New Password
```http
PUT {{base_url}}/auth/update-password
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "current_password": "newsecurepassword456",
  "new_password": "newsecurepassword456"
}
```
**Expected Response**: `400 Bad Request`
```json
{
  "detail": "New password must be different from the current password"
}
```

---

## 👥 Group Management Endpoints

### 1. Create Group

#### Test Case 6.1: Successful Group Creation
```http
POST {{base_url}}/groups/create
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "name": "Family Photos"
}
```
**Expected Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Family Photos",
  "creator_id": 1,
  "invite_code": "ABC123",
  "created_at": "2024-01-15T10:30:00Z"
}
```
**Postman Test Script**:
```javascript
pm.test("Group created successfully", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.environment.set("group_id", jsonData.id);
    pm.environment.set("invite_code", jsonData.invite_code);
});
```

#### Test Case 6.2: Create Group with Empty Name
```http
POST {{base_url}}/groups/create
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "name": ""
}
```
**Expected Response**: `422 Unprocessable Entity`

#### Test Case 6.3: Create Group (Unauthorized)
```http
POST {{base_url}}/groups/create
Content-Type: application/json

{
  "name": "Unauthorized Group"
}
```
**Expected Response**: `401 Unauthorized`

### 2. Join Group

#### Test Case 7.1: Successful Group Join
```http
POST {{base_url}}/groups/join
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "invite_code": "ABC123"
}
```
**Expected Response**: `200 OK`
```json
{
  "message": "Joined group 'Family Photos' successfully."
}
```

#### Test Case 7.2: Join Non-existent Group
```http
POST {{base_url}}/groups/join
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "invite_code": "INVALID"
}
```
**Expected Response**: `404 Not Found`
```json
{
  "detail": "Group not found"
}
```

#### Test Case 7.3: Join Already Joined Group
```http
POST {{base_url}}/groups/join
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "invite_code": "ABC123"
}
```
**Expected Response**: `400 Bad Request`
```json
{
  "detail": "You already joined this group"
}
```

### 3. Get My Groups

#### Test Case 8.1: Get User's Groups
```http
GET {{base_url}}/groups/my
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Family Photos",
    "creator_id": 1,
    "invite_code": "ABC123",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Test Case 8.2: Get Groups (Unauthorized)
```http
GET {{base_url}}/groups/my
```
**Expected Response**: `401 Unauthorized`

### 4. Get Group Details

#### Test Case 9.1: Get Existing Group
```http
GET {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`

#### Test Case 9.2: Get Non-existent Group
```http
GET {{base_url}}/groups/999
Authorization: Bearer {{token}}
```
**Expected Response**: `404 Not Found`

#### Test Case 9.3: Get Group (Not a Member)
```http
GET {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{another_user_token}}
```
**Expected Response**: `403 Forbidden`

### 5. Get Group Members

#### Test Case 10.1: Get Group Members
```http
GET {{base_url}}/groups/{{group_id}}/members
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
{
  "group": "Family Photos",
  "members": [
    {
      "name": "John Doe",
      "bio": "This is my new bio"
    }
  ]
}
```

#### Test Case 10.2: Get Members of Non-existent Group
```http
GET {{base_url}}/groups/999/members
Authorization: Bearer {{token}}
```
**Expected Response**: `404 Not Found`

### 6. Update Group

#### Test Case 11.1: Update Group Name (Owner)
```http
PUT {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "name": "Updated Family Photos"
}
```
**Expected Response**: `200 OK`

#### Test Case 11.2: Update Group (Not Owner)
```http
PUT {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{another_user_token}}
Content-Type: application/json

{
  "name": "Unauthorized Update"
}
```
**Expected Response**: `403 Forbidden`

### 7. Leave Group

#### Test Case 12.1: Leave Group (Member)
```http
DELETE {{base_url}}/groups/{{group_id}}/leave
Authorization: Bearer {{member_token}}
```
**Expected Response**: `200 OK`
```json
{
  "message": "Left group 'Family Photos' successfully"
}
```

#### Test Case 12.2: Leave Group (Owner)
```http
DELETE {{base_url}}/groups/{{group_id}}/leave
Authorization: Bearer {{token}}
```
**Expected Response**: `403 Forbidden`
```json
{
  "detail": "Group creator cannot leave their own group"
}
```

### 8. Delete Group

#### Test Case 13.1: Delete Group (Owner)
```http
DELETE {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
{
  "message": "Group 'Family Photos' deleted successfully"
}
```

#### Test Case 13.2: Delete Group (Not Owner)
```http
DELETE {{base_url}}/groups/{{group_id}}
Authorization: Bearer {{member_token}}
```
**Expected Response**: `403 Forbidden`

---

## 🖼️ Photo Management Endpoints

### 1. Upload Photo

#### Test Case 14.1: Successful Photo Upload
```http
POST {{base_url}}/photos/upload
Authorization: Bearer {{token}}
Content-Type: multipart/form-data

Form Data:
- group_id: {{group_id}}
- file: [Select a JPG/PNG file]
```
**Expected Response**: `200 OK`
```json
{
  "id": 1,
  "group_id": 1,
  "uploader_id": 1,
  "file_path": "uploads/uuid-filename.jpg",
  "created_at": "2024-01-15T10:30:00Z"
}
```
**Postman Test Script**:
```javascript
pm.test("Photo uploaded successfully", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.environment.set("photo_id", jsonData.id);
});
```

#### Test Case 14.2: Upload to Non-member Group
```http
POST {{base_url}}/photos/upload
Authorization: Bearer {{non_member_token}}
Content-Type: multipart/form-data

Form Data:
- group_id: {{group_id}}
- file: [Select a JPG/PNG file]
```
**Expected Response**: `403 Forbidden`

#### Test Case 14.3: Upload Invalid File Format
```http
POST {{base_url}}/photos/upload
Authorization: Bearer {{token}}
Content-Type: multipart/form-data

Form Data:
- group_id: {{group_id}}
- file: [Select a .txt or .pdf file]
```
**Expected Response**: `400 Bad Request`
```json
{
  "detail": "Only JPG and PNG files are allowed."
}
```

### 2. Get Group Photos

#### Test Case 15.1: Get Photos from Group
```http
GET {{base_url}}/photos/group/{{group_id}}
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`
```json
[
  {
    "id": 1,
    "group_id": 1,
    "uploader_id": 1,
    "file_path": "uploads/uuid-filename.jpg",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Test Case 15.2: Get Photos (Not a Member)
```http
GET {{base_url}}/photos/group/{{group_id}}
Authorization: Bearer {{non_member_token}}
```
**Expected Response**: `403 Forbidden`

#### Test Case 15.3: Get Photos from Non-existent Group
```http
GET {{base_url}}/photos/group/999
Authorization: Bearer {{token}}
```
**Expected Response**: `404 Not Found`

### 3. Get Photo Details

#### Test Case 16.1: Get Photo Details
```http
GET {{base_url}}/photos/{{photo_id}}
Authorization: Bearer {{token}}
```
**Expected Response**: `200 OK`

#### Test Case 16.2: Get Non-existent Photo
```http
GET {{base_url}}/photos/999
Authorization: Bearer {{token}}
```
**Expected Response**: `404 Not Found`

#### Test Case 16.3: Get Photo (Not Group Member)
```http
GET {{base_url}}/photos/{{photo_id}}
Authorization: Bearer {{non_member_token}}
```
**Expected Response**: `403 Forbidden`

---

## 🧪 Testing Endpoints

### 1. Get All Groups

#### Test Case 17.1: Get All Groups
```http
GET {{base_url}}/testing/allGroups
```
**Expected Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Family Photos",
    "creator_id": 1,
    "invite_code": "ABC123",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 2. Get All Users

#### Test Case 18.1: Get All Users
```http
GET {{base_url}}/testing/allAppUsers
```
**Expected Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "bio": "This is my new bio",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## 🌐 Root Endpoint

### Test Case 19.1: Root Endpoint
```http
GET {{base_url}}/
```
**Expected Response**: `200 OK`
```json
{
  "message": "Welcome to SnapVault!"
}
```

---

## 📋 Test Execution Order

### Recommended Testing Sequence:

1. **Setup Phase**:
   - Test Case 19.1 (Root endpoint)
   - Test Case 1.1 (Register first user)
   - Test Case 2.1 (Login first user)

2. **User Management**:
   - Test Case 3.1 (Get current user)
   - Test Case 4.1 (Update bio)
   - Test Case 5.1 (Update password)

3. **Group Management**:
   - Test Case 6.1 (Create group)
   - Test Case 8.1 (Get my groups)
   - Test Case 9.1 (Get group details)
   - Test Case 10.1 (Get group members)

4. **Photo Management**:
   - Test Case 14.1 (Upload photo)
   - Test Case 15.1 (Get group photos)
   - Test Case 16.1 (Get photo details)

5. **Multi-user Scenarios**:
   - Register second user
   - Second user joins group
   - Test permissions and restrictions

6. **Error Cases**:
   - Run all negative test cases
   - Test unauthorized access
   - Test invalid data

---

## 🔧 Postman Collection Setup

### Environment Variables to Set:
```json
{
  "base_url": "http://localhost:8000",
  "token": "",
  "user_email": "test@example.com",
  "user_password": "testpassword123",
  "group_id": "",
  "photo_id": "",
  "invite_code": ""
}
```

### Global Test Scripts:
Add this to your collection's Tests tab:
```javascript
pm.test("Response time is less than 1000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(1000);
});

pm.test("Response has correct content type", function () {
    pm.expect(pm.response.headers.get("content-type")).to.include("application/json");
});
```

This comprehensive test suite covers all endpoints with positive and negative test cases, helping you ensure your API works correctly in all scenarios! 