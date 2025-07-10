# 📸 SnapVault Backend API Documentation

## Table of Contents
1. [Project Setup](#project-setup)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Group Management Endpoints](#group-management-endpoints)
   - [Photo Management Endpoints](#photo-management-endpoints)
   - [Testing Endpoints](#testing-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Project Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SnapVault-Backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

---

## Authentication

The API uses JWT (JSON Web Token) based authentication with Bearer token scheme.

### Authentication Flow
1. Register a new user using `/auth/register`
2. Login using `/auth/login` to get an access token
3. Include the token in the `Authorization` header for protected endpoints

### Token Format
```
Authorization: Bearer <your_jwt_token>
```

### Token Expiration
- Access tokens expire after 30 minutes
- You need to login again to get a new token

---

## API Endpoints

### Authentication Endpoints

#### 1. Register User
- **URL**: `POST /auth/register`
- **Description**: Create a new user account
- **Authentication**: Not required
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "bio": "",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```
- **Error Codes**:
  - `400`: Email already exists

#### 2. Login User
- **URL**: `POST /auth/login`
- **Description**: Authenticate user and get access token
- **Authentication**: Not required
- **Request Body**:
  ```json
  {
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
- **Error Codes**:
  - `401`: Invalid credentials

#### 3. Get Current User
- **URL**: `GET /auth/me`
- **Description**: Get current authenticated user's information
- **Authentication**: Required
- **Response**:
  ```json
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "bio": "My bio",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### 4. Update User Bio
- **URL**: `PUT /auth/bio/{updatedBio}`
- **Description**: Update the current user's bio
- **Authentication**: Required
- **Path Parameters**:
  - `updatedBio` (string): New bio text
- **Response**:
  ```json
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "bio": "Updated bio text",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### 5. Update Password
- **URL**: `PUT /auth/update-password`
- **Description**: Update the current user's password
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "current_password": "oldpassword123",
    "new_password": "newpassword456"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Password updated successfully"
  }
  ```
- **Error Codes**:
  - `400`: Current password is incorrect or new password is same as current

### Group Management Endpoints

#### 1. Create Group
- **URL**: `POST /groups/create`
- **Description**: Create a new group with a unique invite code
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "name": "Family Photos"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Family Photos",
    "creator_id": 1,
    "invite_code": "ABC123",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### 2. Join Group
- **URL**: `POST /groups/join`
- **Description**: Join a group using an invite code
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "invite_code": "ABC123"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Joined group 'Family Photos' successfully."
  }
  ```
- **Error Codes**:
  - `404`: Group not found
  - `400`: Already joined this group

#### 3. Get My Groups
- **URL**: `GET /groups/my`
- **Description**: Get all groups the current user is a member of
- **Authentication**: Required
- **Response**:
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

#### 4. Get Group Details
- **URL**: `GET /groups/{id}`
- **Description**: Get details of a specific group (must be a member)
- **Authentication**: Required
- **Path Parameters**:
  - `id` (integer): Group ID
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Family Photos",
    "creator_id": 1,
    "invite_code": "ABC123",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```
- **Error Codes**:
  - `404`: Group not found
  - `403`: Not a member of this group

#### 5. Get Group Members
- **URL**: `GET /groups/{id}/members`
- **Description**: Get all members of a specific group
- **Authentication**: Required
- **Path Parameters**:
  - `id` (integer): Group ID
- **Response**:
  ```json
  {
    "group": "Family Photos",
    "members": [
      {
        "name": "John Doe",
        "bio": "My bio"
      },
      {
        "name": "Jane Smith",
        "bio": "Another bio"
      }
    ]
  }
  ```
- **Error Codes**:
  - `404`: Group not found

#### 6. Leave Group
- **URL**: `DELETE /groups/{id}/leave`
- **Description**: Leave a group (group creator cannot leave)
- **Authentication**: Required
- **Path Parameters**:
  - `id` (integer): Group ID
- **Response**:
  ```json
  {
    "message": "Left group 'Family Photos' successfully"
  }
  ```
- **Error Codes**:
  - `404`: Group not found
  - `400`: Not a member of this group
  - `403`: Group creator cannot leave

#### 7. Delete Group
- **URL**: `DELETE /groups/{id}`
- **Description**: Delete a group (only group creator can delete)
- **Authentication**: Required
- **Path Parameters**:
  - `id` (integer): Group ID
- **Response**:
  ```json
  {
    "message": "Group 'Family Photos' deleted successfully"
  }
  ```
- **Error Codes**:
  - `404`: Group not found
  - `403`: Only group creator can delete

#### 8. Update Group
- **URL**: `PUT /groups/{id}`
- **Description**: Update group name (only group creator can update)
- **Authentication**: Required
- **Path Parameters**:
  - `id` (integer): Group ID
- **Request Body**:
  ```json
  {
    "name": "Updated Group Name"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Updated Group Name",
    "creator_id": 1,
    "invite_code": "ABC123",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```
- **Error Codes**:
  - `404`: Group not found
  - `403`: Only group creator can update

### Photo Management Endpoints

#### 1. Upload Photo
- **URL**: `POST /photos/upload`
- **Description**: Upload a photo to a group
- **Authentication**: Required
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `group_id` (integer): ID of the group to upload to
  - `file` (file): Image file (JPG, JPEG, PNG only)
- **Response**:
  ```json
  {
    "id": 1,
    "group_id": 1,
    "uploader_id": 1,
    "file_path": "uploads/85ba18b9-1b05-46b6-9fb6-d15fd30e6824.jpg",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```
- **Error Codes**:
  - `403`: Not a member of this group
  - `400`: Invalid file format

#### 2. Get Group Photos
- **URL**: `GET /photos/group/{group_id}`
- **Description**: Get all photos in a specific group
- **Authentication**: Required
- **Path Parameters**:
  - `group_id` (integer): Group ID
- **Response**:
  ```json
  [
    {
      "id": 1,
      "group_id": 1,
      "uploader_id": 1,
      "file_path": "uploads/85ba18b9-1b05-46b6-9fb6-d15fd30e6824.jpg",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
  ```
- **Error Codes**:
  - `404`: Group not found
  - `403`: Not a member of this group

#### 3. Get Photo
- **URL**: `GET /photos/{photo_id}`
- **Description**: Get details of a specific photo
- **Authentication**: Required
- **Path Parameters**:
  - `photo_id` (integer): Photo ID
- **Response**:
  ```json
  {
    "id": 1,
    "group_id": 1,
    "uploader_id": 1,
    "file_path": "uploads/85ba18b9-1b05-46b6-9fb6-d15fd30e6824.jpg",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```
- **Error Codes**:
  - `404`: Photo not found
  - `403`: Not allowed to view this photo

### Testing Endpoints

⚠️ **Note**: These endpoints are for development/testing purposes only and should not be used in production.

#### 1. Get All Groups
- **URL**: `GET /testing/allGroups`
- **Description**: Get all groups in the system (testing only)
- **Authentication**: Not required
- **Response**: Array of all groups

#### 2. Get All Users
- **URL**: `GET /testing/allAppUsers`
- **Description**: Get all users in the system (testing only)
- **Authentication**: Not required
- **Response**: Array of all users

---

## Data Models

### User Model
```json
{
  "id": "integer",
  "name": "string",
  "email": "string",
  "bio": "string (optional)",
  "hashed_password": "string",
  "face_embedding": "string (optional)",
  "created_at": "datetime"
}
```

### Group Model
```json
{
  "id": "integer",
  "name": "string",
  "creator_id": "integer",
  "invite_code": "string",
  "created_at": "datetime"
}
```

### Photo Model
```json
{
  "id": "integer",
  "group_id": "integer",
  "uploader_id": "integer",
  "file_path": "string",
  "created_at": "datetime"
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns error messages in JSON format:

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Error message describing the issue"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 403 Forbidden
```json
{
  "detail": "You are not a member of this group"
}
```

#### 404 Not Found
```json
{
  "detail": "Group not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Examples

### Complete Authentication Flow

1. **Register a new user**:
   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "John Doe",
          "email": "john@example.com",
          "password": "securepassword123"
        }'
   ```

2. **Login to get token**:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
          "email": "john@example.com",
          "password": "securepassword123"
        }'
   ```

3. **Use token for authenticated requests**:
   ```bash
   curl -X GET "http://localhost:8000/auth/me" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
   ```

### Group Management Example

1. **Create a group**:
   ```bash
   curl -X POST "http://localhost:8000/groups/create" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "Family Photos"
        }'
   ```

2. **Join a group**:
   ```bash
   curl -X POST "http://localhost:8000/groups/join" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
        -H "Content-Type: application/json" \
        -d '{
          "invite_code": "ABC123"
        }'
   ```

### Photo Upload Example

```bash
curl -X POST "http://localhost:8000/photos/upload" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
     -F "group_id=1" \
     -F "file=@/path/to/your/photo.jpg"
```

---

## Development Notes

### Database
- The application uses SQLite as the database
- Database file: `snapvault.db`
- Tables are automatically created on first run

### File Storage
- Uploaded photos are stored in the `uploads/` directory
- Files are renamed with UUID to prevent conflicts
- Supported formats: JPG, JPEG, PNG

### Security
- Passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes
- All sensitive endpoints require authentication

### Future Enhancements
- Face recognition using InsightFace
- Real-time notifications
- Admin dashboard
- WhatsApp/SMS integration 