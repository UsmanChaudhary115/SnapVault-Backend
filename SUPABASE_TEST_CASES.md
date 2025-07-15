# SnapVault Supabase API Test Cases

## Overview

This document provides comprehensive test cases for all SnapVault Supabase API endpoints. The test cases cover both positive and negative scenarios, including edge cases and security considerations.

### Test Environment Setup

```bash
# Prerequisites
- Python 3.8+
- FastAPI application running on localhost:8000
- Supabase instance configured
- Test database with sample data
- Valid test user credentials
```

### Test Data Setup

```python
# Test Users
TEST_USERS = {
    "admin": {"email": "admin@test.com", "password": "admin123", "name": "Admin User"},
    "user1": {"email": "user1@test.com", "password": "user123", "name": "Test User 1"},
    "user2": {"email": "user2@test.com", "password": "user123", "name": "Test User 2"}
}

# Test Files
TEST_FILES = {
    "valid_image": "test_photo.jpg",  # Valid JPEG, < 10MB
    "large_image": "large_photo.jpg",  # Valid JPEG, > 10MB
    "invalid_file": "document.pdf",   # Invalid type
    "profile_pic": "profile.png"      # Valid PNG, < 5MB
}
```

---

## Authentication Test Cases

### 1. Supabase Registration Tests

#### TC_AUTH_001: Valid Registration
```python
def test_supabase_register_valid():
    """Test successful user registration with Supabase"""
    url = "http://localhost:8000/auth/supabase_register"
    data = {
        "name": "John Doe",
        "email": "john.doe@test.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(url, data=data)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["email"] == "john.doe@test.com"
    assert response.json()["name"] == "John Doe"
    assert "supabase_user_id" in response.json()
```

#### TC_AUTH_002: Invalid Email Registration
```python
def test_supabase_register_invalid_email():
    """Test registration with invalid email format"""
    url = "http://localhost:8000/auth/supabase_register"
    data = {
        "name": "John Doe",
        "email": "invalid-email",
        "password": "SecurePass123!"
    }
    
    response = requests.post(url, data=data)
    
    assert response.status_code == 400
    assert "Invalid email format" in response.json()["detail"]
```

#### TC_AUTH_003: Duplicate Email Registration
```python
def test_supabase_register_duplicate_email():
    """Test registration with already existing email"""
    url = "http://localhost:8000/auth/supabase_register"
    data = {
        "name": "Jane Doe",
        "email": "john.doe@test.com",  # Already registered
        "password": "SecurePass123!"
    }
    
    response = requests.post(url, data=data)
    
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]
```

### 2. Supabase Login Tests

#### TC_AUTH_004: Valid Login
```python
def test_supabase_login_valid():
    """Test successful login with valid credentials"""
    url = "http://localhost:8000/auth/supabase_login"
    data = {
        "email": "john.doe@test.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(url, json=data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert "user" in response.json()
```

#### TC_AUTH_005: Invalid Credentials Login
```python
def test_supabase_login_invalid_credentials():
    """Test login with invalid password"""
    url = "http://localhost:8000/auth/supabase_login"
    data = {
        "email": "john.doe@test.com",
        "password": "WrongPassword"
    }
    
    response = requests.post(url, json=data)
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
```

### 3. Google OAuth Tests

#### TC_AUTH_006: Google OAuth URL Generation
```python
def test_google_oauth_url():
    """Test Google OAuth URL generation"""
    url = "http://localhost:8000/auth/supabase_google"
    
    response = requests.get(url)
    
    assert response.status_code == 200
    assert "auth_url" in response.json()
    assert "supabase" in response.json()["auth_url"]
```

---

## User Management Test Cases

### 1. Profile Management Tests

#### TC_USER_001: Get User Profile
```python
def test_get_user_profile():
    """Test retrieving current user profile"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/user/supabase_profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert "name" in response.json()
    assert "email" in response.json()
```

#### TC_USER_002: Update Bio
```python
def test_update_user_bio():
    """Test updating user bio"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/user/supabase_bio/Love%20photography%20and%20travel"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(url, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["bio"] == "Love photography and travel"
```

#### TC_USER_003: Update Bio Too Long
```python
def test_update_user_bio_too_long():
    """Test updating bio with text exceeding limit"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    long_bio = "a" * 501  # Exceeds 500 character limit
    url = f"http://localhost:8000/user/supabase_bio/{long_bio}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(url, headers=headers)
    
    assert response.status_code == 400
    assert "cannot exceed 500 characters" in response.json()["detail"]
```

#### TC_USER_004: Update Profile Picture
```python
def test_update_profile_picture():
    """Test uploading new profile picture"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/user/supabase_profile_picture"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_profile.jpg", "rb") as f:
        files = {"file": f}
        response = requests.put(url, headers=headers, files=files)
    
    assert response.status_code == 200
    assert "profile_picture" in response.json()
    assert response.json()["profile_picture"] is not None
```

#### TC_USER_005: Upload Invalid Profile Picture
```python
def test_upload_invalid_profile_picture():
    """Test uploading invalid file type as profile picture"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/user/supabase_profile_picture"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_document.pdf", "rb") as f:
        files = {"file": f}
        response = requests.put(url, headers=headers, files=files)
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
```

### 2. Storage Statistics Tests

#### TC_USER_006: Get Storage Statistics
```python
def test_get_storage_statistics():
    """Test retrieving user storage statistics"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/user/supabase_storage_stats"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert "total_storage_bytes" in response.json()
    assert "storage_limit_bytes" in response.json()
    assert "storage_used_percentage" in response.json()
```

---

## Group Management Test Cases

### 1. Group Creation Tests

#### TC_GROUP_001: Create Valid Group
```python
def test_create_group_valid():
    """Test creating a group with valid data"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/groups/supabase_create"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Family Vacation 2024",
        "description": "Our summer vacation photos"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 200
    assert response.json()["name"] == "Family Vacation 2024"
    assert "invite_code" in response.json()
    assert len(response.json()["invite_code"]) == 6
```

#### TC_GROUP_002: Create Group Invalid Name
```python
def test_create_group_invalid_name():
    """Test creating group with invalid name"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/groups/supabase_create"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "A",  # Too short
        "description": "Test group"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 400
    assert "at least 2 characters" in response.json()["detail"]
```

### 2. Group Membership Tests

#### TC_GROUP_003: Join Group Valid Code
```python
def test_join_group_valid_code():
    """Test joining group with valid invite code"""
    # First create a group to get invite code
    group_data = create_test_group()
    invite_code = group_data["invite_code"]
    
    # Join with different user
    token = get_auth_token("user1@test.com", "user123")
    url = "http://localhost:8000/groups/supabase_join"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"invite_code": invite_code}
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 200
    assert "Successfully joined group" in response.json()["message"]
    assert response.json()["role"] == "restricted-viewer"
```

#### TC_GROUP_004: Join Group Invalid Code
```python
def test_join_group_invalid_code():
    """Test joining group with invalid invite code"""
    token = get_auth_token("user1@test.com", "user123")
    url = "http://localhost:8000/groups/supabase_join"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"invite_code": "INVALID"}
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 404
    assert "Invalid invite code" in response.json()["detail"]
```

#### TC_GROUP_005: Join Group Already Member
```python
def test_join_group_already_member():
    """Test joining group user is already member of"""
    group_data = create_test_group()
    invite_code = group_data["invite_code"]
    
    # Creator tries to join their own group
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/groups/supabase_join"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"invite_code": invite_code}
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]
```

### 3. Group Analytics Tests

#### TC_GROUP_006: Get Group Analytics Admin
```python
def test_get_group_analytics_admin():
    """Test getting group analytics as admin"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = f"http://localhost:8000/groups/supabase_group/{group_id}/analytics?days=30"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert "basic_stats" in response.json()
    assert "member_roles" in response.json()
    assert "top_contributors" in response.json()
```

#### TC_GROUP_007: Get Group Analytics Non-Admin
```python
def test_get_group_analytics_non_admin():
    """Test getting group analytics as non-admin"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Join as regular user
    join_group_as_user(group_data["invite_code"], "user1@test.com")
    
    token = get_auth_token("user1@test.com", "user123")
    url = f"http://localhost:8000/groups/supabase_group/{group_id}/analytics"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 403
    assert "Only group admin or owner" in response.json()["detail"]
```

---

## Photo Management Test Cases

### 1. Photo Upload Tests

#### TC_PHOTO_001: Upload Valid Photo
```python
def test_upload_photo_valid():
    """Test uploading valid photo to group"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_photo.jpg", "rb") as f:
        files = {"file": f}
        data = {
            "group_id": group_id,
            "tags": "vacation,beach,family",
            "description": "Beautiful sunset"
        }
        response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["group_id"] == group_id
    assert "file_url" in response.json()
```

#### TC_PHOTO_002: Upload Photo No Permission
```python
def test_upload_photo_no_permission():
    """Test uploading photo without permission"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # User not in group tries to upload
    token = get_auth_token("user2@test.com", "user123")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_photo.jpg", "rb") as f:
        files = {"file": f}
        data = {"group_id": group_id}
        response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 403
    assert "not a member" in response.json()["detail"]
```

#### TC_PHOTO_003: Upload Invalid File Type
```python
def test_upload_invalid_file_type():
    """Test uploading invalid file type"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_document.pdf", "rb") as f:
        files = {"file": f}
        data = {"group_id": group_id}
        response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
```

#### TC_PHOTO_004: Upload File Too Large
```python
def test_upload_file_too_large():
    """Test uploading file exceeding size limit"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a file > 10MB (mock large file)
    large_content = b"0" * (11 * 1024 * 1024)  # 11MB
    
    files = {"file": ("large.jpg", large_content, "image/jpeg")}
    data = {"group_id": group_id}
    response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 400
    assert "exceed 10MB" in response.json()["detail"]
```

### 2. Batch Upload Tests

#### TC_PHOTO_005: Batch Upload Valid
```python
def test_batch_upload_valid():
    """Test batch uploading multiple valid photos"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload_batch"
    headers = {"Authorization": f"Bearer {token}"}
    
    files = [
        ("files", ("photo1.jpg", open("test_photo1.jpg", "rb"), "image/jpeg")),
        ("files", ("photo2.jpg", open("test_photo2.jpg", "rb"), "image/jpeg"))
    ]
    data = {"group_id": group_id}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 200
    assert response.json()["total_files"] == 2
    assert response.json()["successful_uploads"] >= 0
```

#### TC_PHOTO_006: Batch Upload Too Many Files
```python
def test_batch_upload_too_many_files():
    """Test batch uploading more than allowed files"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload_batch"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create 21 files (exceeds limit of 20)
    files = []
    for i in range(21):
        files.append(("files", (f"photo{i}.jpg", b"fake_content", "image/jpeg")))
    
    data = {"group_id": group_id}
    response = requests.post(url, headers=headers, files=files, data=data)
    
    assert response.status_code == 400
    assert "more than 20 files" in response.json()["detail"]
```

### 3. Photo Retrieval Tests

#### TC_PHOTO_007: Get Group Photos
```python
def test_get_group_photos():
    """Test retrieving photos from group"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Upload a photo first
    upload_test_photo(group_id)
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = f"http://localhost:8000/photos/supabase_group/{group_id}?limit=10"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

#### TC_PHOTO_008: Get Group Photos With Filters
```python
def test_get_group_photos_with_filters():
    """Test retrieving photos with filters"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Upload photos with tags
    upload_test_photo(group_id, tags="vacation,beach")
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = f"http://localhost:8000/photos/supabase_group/{group_id}?tags=vacation&limit=5"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 4. Photo Analytics Tests

#### TC_PHOTO_009: Get Photo Analytics
```python
def test_get_photo_analytics():
    """Test getting photo analytics for group"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Upload some photos
    upload_test_photo(group_id)
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = f"http://localhost:8000/photos/supabase_analytics/group/{group_id}?days=30"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "total_photos" in response.json()["summary"]
```

### 5. Batch Tag Tests

#### TC_PHOTO_010: Batch Tag Photos
```python
def test_batch_tag_photos():
    """Test adding tags to multiple photos"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Upload photos
    photo1_id = upload_test_photo(group_id)["id"]
    photo2_id = upload_test_photo(group_id)["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_batch_tag"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "photo_ids": [photo1_id, photo2_id],
        "tags": ["summer", "vacation", "2024"]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    assert response.status_code == 200
    assert response.json()["successful_updates"] >= 0
```

---

## Security Test Cases

### 1. Authentication Security Tests

#### TC_SEC_001: JWT Token Expiration
```python
def test_jwt_token_expiration():
    """Test that expired JWT tokens are rejected"""
    # Use an expired token
    expired_token = "expired_jwt_token_here"
    url = "http://localhost:8000/user/supabase_profile"
    headers = {"Authorization": f"Bearer {expired_token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 401
```

#### TC_SEC_002: Invalid JWT Token
```python
def test_invalid_jwt_token():
    """Test that invalid JWT tokens are rejected"""
    invalid_token = "invalid.jwt.token"
    url = "http://localhost:8000/user/supabase_profile"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 401
```

### 2. Authorization Security Tests

#### TC_SEC_003: Access Other User Data
```python
def test_access_other_user_data():
    """Test that users cannot access other users' private data"""
    # User 1 tries to delete User 2's account
    token1 = get_auth_token("user1@test.com", "user123")
    user2_id = get_user_id("user2@test.com")
    
    url = f"http://localhost:8000/auth/supabase_delete-account-by-id/{user2_id}"
    headers = {"Authorization": f"Bearer {token1}"}
    
    response = requests.delete(url, headers=headers)
    
    assert response.status_code == 403
    assert "only delete your own account" in response.json()["detail"]
```

### 3. File Upload Security Tests

#### TC_SEC_004: Malicious File Upload
```python
def test_malicious_file_upload():
    """Test that malicious files are rejected"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to upload a script file with image extension
    malicious_content = b"<?php echo 'malicious code'; ?>"
    files = {"file": ("malicious.jpg", malicious_content, "image/jpeg")}
    data = {"group_id": group_id}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    # Should be rejected based on content validation
    assert response.status_code == 400
```

---

## Performance Test Cases

### 1. Load Testing

#### TC_PERF_001: Concurrent Photo Uploads
```python
import threading
import time

def test_concurrent_photo_uploads():
    """Test system performance under concurrent photo uploads"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    def upload_photo():
        token = get_auth_token("john.doe@test.com", "SecurePass123!")
        url = "http://localhost:8000/photos/supabase_upload"
        headers = {"Authorization": f"Bearer {token}"}
        
        with open("test_photo.jpg", "rb") as f:
            files = {"file": f}
            data = {"group_id": group_id}
            response = requests.post(url, headers=headers, files=files, data=data)
            return response.status_code
    
    # Create 10 concurrent uploads
    threads = []
    results = []
    
    start_time = time.time()
    
    for i in range(10):
        thread = threading.Thread(target=lambda: results.append(upload_photo()))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # Check that most uploads succeeded
    success_count = sum(1 for status in results if status == 200)
    assert success_count >= 8  # Allow for some failures under load
    assert end_time - start_time < 30  # Should complete within 30 seconds
```

### 2. Large Dataset Tests

#### TC_PERF_002: Large Group Photo Retrieval
```python
def test_large_group_photo_retrieval():
    """Test retrieving photos from group with many photos"""
    group_data = create_test_group()
    group_id = group_data["id"]
    
    # Upload many photos (simulate large dataset)
    for i in range(100):
        upload_test_photo(group_id, description=f"Photo {i}")
    
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = f"http://localhost:8000/photos/supabase_group/{group_id}?limit=50&offset=0"
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    response = requests.get(url, headers=headers)
    end_time = time.time()
    
    assert response.status_code == 200
    assert len(response.json()) <= 50
    assert end_time - start_time < 5  # Should respond within 5 seconds
```

---

## Integration Test Cases

### 1. End-to-End Workflow Tests

#### TC_INT_001: Complete Photo Sharing Workflow
```python
def test_complete_photo_sharing_workflow():
    """Test complete workflow from registration to photo sharing"""
    
    # 1. Register two users
    register_user("alice@test.com", "Alice", "password123")
    register_user("bob@test.com", "Bob", "password123")
    
    # 2. Alice creates a group
    alice_token = get_auth_token("alice@test.com", "password123")
    group_data = create_group_as_user(alice_token, "Alice's Photos", "My photo collection")
    
    # 3. Bob joins the group
    bob_token = get_auth_token("bob@test.com", "password123")
    join_group_as_user(group_data["invite_code"], bob_token)
    
    # 4. Alice uploads photos
    photo_data = upload_photo_as_user(alice_token, group_data["id"], "vacation.jpg")
    
    # 5. Bob views the photos
    photos = get_group_photos_as_user(bob_token, group_data["id"])
    
    # 6. Alice gets analytics
    analytics = get_group_analytics_as_user(alice_token, group_data["id"])
    
    # Verify the complete workflow
    assert len(photos) >= 1
    assert analytics["basic_stats"]["total_photos"] >= 1
    assert analytics["basic_stats"]["total_members"] == 2
```

### 2. Supabase Sync Tests

#### TC_INT_002: Supabase Data Synchronization
```python
def test_supabase_data_sync():
    """Test that data is properly synchronized with Supabase"""
    
    # Create group and upload photo
    group_data = create_test_group()
    photo_data = upload_test_photo(group_data["id"])
    
    # Verify data exists in Supabase (mock check)
    supabase_client = get_supabase_client()
    
    # Check group sync
    group_result = supabase_client.table("groups").select("*").eq("id", group_data["id"]).execute()
    assert len(group_result.data) == 1
    
    # Check photo sync
    photo_result = supabase_client.table("photos").select("*").eq("id", photo_data["id"]).execute()
    assert len(photo_result.data) == 1
```

---

## Helper Functions

```python
def get_auth_token(email: str, password: str) -> str:
    """Get authentication token for user"""
    url = "http://localhost:8000/auth/supabase_login"
    data = {"email": email, "password": password}
    response = requests.post(url, json=data)
    return response.json()["access_token"]

def create_test_group() -> dict:
    """Create a test group and return group data"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/groups/supabase_create"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Group", "description": "Test group for testing"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def upload_test_photo(group_id: int, tags: str = None, description: str = None) -> dict:
    """Upload a test photo to a group"""
    token = get_auth_token("john.doe@test.com", "SecurePass123!")
    url = "http://localhost:8000/photos/supabase_upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_photo.jpg", "rb") as f:
        files = {"file": f}
        data = {"group_id": group_id}
        if tags:
            data["tags"] = tags
        if description:
            data["description"] = description
        response = requests.post(url, headers=headers, files=files, data=data)
    
    return response.json()

def register_user(email: str, name: str, password: str) -> dict:
    """Register a new user"""
    url = "http://localhost:8000/auth/supabase_register"
    data = {"name": name, "email": email, "password": password}
    response = requests.post(url, data=data)
    return response.json()

def cleanup_test_data():
    """Clean up test data after tests"""
    # Delete test users, groups, and files
    # Implementation depends on your cleanup strategy
    pass
```

---

## Test Execution

### Running Tests

```bash
# Install test dependencies
pip install pytest requests pytest-asyncio

# Run all tests
pytest test_supabase_api.py -v

# Run specific test categories
pytest test_supabase_api.py::test_auth -v
pytest test_supabase_api.py::test_groups -v
pytest test_supabase_api.py::test_photos -v

# Run with coverage
pytest test_supabase_api.py --cov=routes --cov-report=html

# Run performance tests
pytest test_supabase_api.py::test_performance -v --tb=short
```

### Test Configuration

```python
# conftest.py
import pytest
import requests
import os

@pytest.fixture(scope="session")
def test_client():
    """Create test client for the session"""
    return requests.Session()

@pytest.fixture(scope="function")
def clean_db():
    """Clean database before each test"""
    # Implement database cleanup
    yield
    # Cleanup after test
    cleanup_test_data()

@pytest.fixture
def test_user():
    """Create a test user for the test"""
    user_data = register_user("test@example.com", "Test User", "testpass123")
    yield user_data
    # Cleanup user after test
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest requests pytest-asyncio
      - name: Run tests
        run: pytest test_supabase_api.py -v
```

---

## Test Results and Reporting

### Expected Test Coverage

- **Authentication**: 95%+ coverage
- **User Management**: 90%+ coverage  
- **Group Management**: 95%+ coverage
- **Photo Management**: 90%+ coverage
- **Security**: 100% coverage for security-critical paths

### Test Report Format

```
Test Results Summary:
=====================
Total Tests: 50
Passed: 48
Failed: 2
Skipped: 0
Coverage: 92.5%

Failed Tests:
- TC_PHOTO_004: Upload File Too Large (Network timeout)
- TC_PERF_001: Concurrent Photo Uploads (Performance degradation)

Performance Metrics:
- Average API Response Time: 245ms
- 95th Percentile Response Time: 1.2s
- Upload Success Rate: 98.5%
``` 