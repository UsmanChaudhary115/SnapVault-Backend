# SnapVault Supabase API Documentation

## Overview

This document provides comprehensive documentation for SnapVault's Supabase-integrated API endpoints. These endpoints offer enhanced functionality with cloud synchronization, advanced analytics, and modular storage support.

### Key Features

- **Dual Architecture**: Local and Supabase routes coexist for maximum flexibility
- **Cloud Synchronization**: All Supabase endpoints sync data to Supabase for backup and real-time features
- **Modular Storage**: File storage system that can switch between local and S3 storage
- **Enhanced Analytics**: Advanced statistics and reporting capabilities
- **Professional Documentation**: Complete API reference with examples

### Base URL

```
http://localhost:8000
```

### Authentication

All Supabase endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Supabase Authentication Endpoints

### 1. Google OAuth Login

**Endpoint**: `GET /auth/supabase_google`

**Description**: Initiate Google OAuth login flow

**Response**:
```json
{
  "auth_url": "https://supabase-oauth-url..."
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/auth/supabase_google"
```

### 2. Google OAuth Callback

**Endpoint**: `GET /auth/supabase_google/callback`

**Parameters**:
- `access_token` (string): Access token from OAuth flow
- `refresh_token` (string, optional): Refresh token

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "supabase_user_id": "uuid-here"
  }
}
```

### 3. Supabase Registration

**Endpoint**: `POST /auth/supabase_register`

**Form Data**:
- `name` (string): Full name
- `email` (string): Email address
- `password` (string): Password

**Response**:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "supabase_user_id": "uuid-here",
  "auth_provider": "email"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/auth/supabase_register" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "password=securepassword123"
```

### 4. Supabase Login

**Endpoint**: `POST /auth/supabase_login`

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

## Supabase User Endpoints

### 1. Get User Profile

**Endpoint**: `GET /user/supabase_profile`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "bio": "Software developer",
  "profile_picture": "/uploads/profile_pictures/uuid.jpg",
  "supabase_user_id": "uuid-here"
}
```

### 2. Update Bio

**Endpoint**: `PUT /user/supabase_bio/{updated_bio}`

**Parameters**:
- `updated_bio` (string): New bio text (max 500 characters)

**Example**:
```bash
curl -X PUT "http://localhost:8000/user/supabase_bio/Love%20photography!" \
  -H "Authorization: Bearer <token>"
```

### 3. Update Name

**Endpoint**: `PUT /user/supabase_name/{name}`

**Parameters**:
- `name` (string): New display name (2-100 characters)

**Example**:
```bash
curl -X PUT "http://localhost:8000/user/supabase_name/Jane%20Smith" \
  -H "Authorization: Bearer <token>"
```

### 4. Update Profile Picture

**Endpoint**: `PUT /user/supabase_profile_picture`

**Form Data**:
- `file` (file): Image file (JPEG, PNG, GIF, WebP, max 5MB)

**Example**:
```bash
curl -X PUT "http://localhost:8000/user/supabase_profile_picture" \
  -H "Authorization: Bearer <token>" \
  -F "file=@profile.jpg"
```

### 5. Get Storage Statistics

**Endpoint**: `GET /user/supabase_storage_stats`

**Response**:
```json
{
  "user_id": 1,
  "profile_picture_size": 1048576,
  "total_photos": 25,
  "total_storage_bytes": 52428800,
  "storage_limit_bytes": 104857600,
  "storage_used_percentage": 50.0
}
```

---

## Supabase Group Endpoints

### 1. Create Group

**Endpoint**: `POST /groups/supabase_create`

**Request Body**:
```json
{
  "name": "Family Vacation 2024",
  "description": "Our amazing summer vacation photos"
}
```

**Response**:
```json
{
  "id": 5,
  "name": "Family Vacation 2024",
  "description": "Our amazing summer vacation photos",
  "creator_id": 1,
  "invite_code": "ABC123",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Join Group

**Endpoint**: `POST /groups/supabase_join`

**Request Body**:
```json
{
  "invite_code": "ABC123"
}
```

**Response**:
```json
{
  "message": "Successfully joined group 'Family Vacation 2024'",
  "group": {
    "id": 5,
    "name": "Family Vacation 2024",
    "description": "Our amazing summer vacation photos",
    "invite_code": "ABC123"
  },
  "role": "restricted-viewer"
}
```

### 3. Get My Groups

**Endpoint**: `GET /groups/supabase_my`

**Query Parameters**:
- `include_stats` (boolean): Include group statistics

**Response**:
```json
[
  {
    "id": 5,
    "name": "Family Vacation 2024",
    "description": "Our amazing summer vacation photos",
    "creator_id": 1,
    "invite_code": "ABC123",
    "user_role_id": 1,
    "stats": {
      "total_photos": 42,
      "total_members": 6
    }
  }
]
```

### 4. Get Group Analytics

**Endpoint**: `GET /groups/supabase_group/{group_id}/analytics`

**Parameters**:
- `group_id` (integer): Group ID
- `days` (integer): Number of days for analytics (1-365)

**Response**:
```json
{
  "group_id": 5,
  "group_name": "Family Vacation 2024",
  "period_days": 30,
  "basic_stats": {
    "total_members": 6,
    "total_photos": 42,
    "recent_photos": 15,
    "total_storage_bytes": 67108864,
    "storage_mb": 64.0
  },
  "member_roles": {
    "super-admin": 1,
    "admin": 1,
    "contributor": 2,
    "viewer": 2
  },
  "top_contributors": [
    {"name": "John Doe", "photo_count": 18},
    {"name": "Jane Smith", "photo_count": 12}
  ],
  "activity_summary": {
    "photos_per_day": 0.5,
    "average_photos_per_member": 7.0
  }
}
```

---

## Supabase Photo Endpoints

### 1. Upload Photo

**Endpoint**: `POST /photos/supabase_upload`

**Form Data**:
- `group_id` (integer): Target group ID
- `file` (file): Image file (JPEG, PNG, GIF, WebP, max 10MB)
- `tags` (string, optional): Comma-separated tags
- `description` (string, optional): Photo description

**Response**:
```json
{
  "id": 123,
  "group_id": 5,
  "uploader_id": 1,
  "file_path": "/uploads/photos/uuid.jpg",
  "file_url": "/uploads/photos/uuid.jpg",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "original_filename": "vacation.jpg",
    "file_size": 2048576,
    "mime_type": "image/jpeg",
    "tags": ["vacation", "beach", "family"],
    "description": "Beautiful sunset at the beach"
  }
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/photos/supabase_upload" \
  -H "Authorization: Bearer <token>" \
  -F "group_id=5" \
  -F "file=@vacation.jpg" \
  -F "tags=vacation,beach,family" \
  -F "description=Beautiful sunset at the beach"
```

### 2. Batch Upload Photos

**Endpoint**: `POST /photos/supabase_upload_batch`

**Form Data**:
- `group_id` (integer): Target group ID
- `files` (files[]): Array of image files (max 20 files)

**Response**:
```json
{
  "group_id": 5,
  "total_files": 3,
  "successful_uploads": 2,
  "failed_uploads": 1,
  "results": {
    "successful": [
      {
        "filename": "photo1.jpg",
        "photo_id": 124,
        "file_url": "/uploads/photos/uuid1.jpg"
      },
      {
        "filename": "photo2.jpg",
        "photo_id": 125,
        "file_url": "/uploads/photos/uuid2.jpg"
      }
    ],
    "failed": [
      {
        "filename": "photo3.gif",
        "error": "File size exceeds 10MB"
      }
    ]
  }
}
```

### 3. Get Group Photos

**Endpoint**: `GET /photos/supabase_group/{group_id}`

**Query Parameters**:
- `limit` (integer): Number of photos to return (1-100, default: 50)
- `offset` (integer): Number of photos to skip (default: 0)
- `sort_by` (string): Sort field (uploaded_at, file_size)
- `sort_order` (string): Sort order (asc, desc)
- `tags` (string): Filter by tags (comma-separated)
- `uploader_id` (integer): Filter by uploader
- `date_from` (string): Filter from date (YYYY-MM-DD)
- `date_to` (string): Filter to date (YYYY-MM-DD)

**Response**:
```json
[
  {
    "id": 123,
    "group_id": 5,
    "uploader_id": 1,
    "file_path": "/uploads/photos/uuid.jpg",
    "file_url": "/uploads/photos/uuid.jpg",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "uploader_name": "John Doe",
    "metadata": {
      "tags": ["vacation", "beach"],
      "description": "Beautiful sunset"
    }
  }
]
```

### 4. Get Photo Analytics

**Endpoint**: `GET /photos/supabase_analytics/group/{group_id}`

**Query Parameters**:
- `days` (integer): Number of days for analytics (1-365, default: 30)

**Response**:
```json
{
  "group_id": 5,
  "period_days": 30,
  "summary": {
    "total_photos": 42,
    "recent_photos": 15,
    "total_storage_bytes": 67108864,
    "storage_mb": 64.0,
    "photos_per_day": 0.5
  },
  "top_uploaders": [
    {"name": "John Doe", "photo_count": 18},
    {"name": "Jane Smith", "photo_count": 12}
  ],
  "daily_uploads": [
    {"date": "2024-01-15", "photo_count": 3},
    {"date": "2024-01-14", "photo_count": 1}
  ]
}
```

### 5. Batch Tag Photos

**Endpoint**: `POST /photos/supabase_batch_tag`

**Request Body**:
```json
{
  "photo_ids": [123, 124, 125],
  "tags": ["summer", "vacation", "2024"]
}
```

**Response**:
```json
{
  "total_photos": 3,
  "successful_updates": 2,
  "failed_updates": 1,
  "tags_added": ["summer", "vacation", "2024"],
  "failures": [
    {
      "photo_id": 125,
      "error": "No permission"
    }
  ]
}
```

---

## Storage Configuration

### Environment Variables

Configure storage backend using environment variables:

```bash
# Storage Type (local or s3)
STORAGE_TYPE=local

# Local Storage Configuration
UPLOAD_DIRECTORY=uploads

# S3 Configuration (when STORAGE_TYPE=s3)
S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

### Switching to S3 Storage

To switch from local storage to S3:

1. Set environment variables:
```bash
export STORAGE_TYPE=s3
export S3_BUCKET_NAME=your-snapvault-bucket
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

2. Implement S3 storage handler (currently placeholder):
   - Complete the `S3StorageHandler` class in `utils/storage.py`
   - Add boto3 dependency to requirements.txt
   - Implement file upload, deletion, and URL generation

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (duplicate resource)
- **422**: Unprocessable Entity (validation error)
- **500**: Internal Server Error

### Permission Levels

#### Group Roles
1. **Super Admin (1)**: Full group control, ownership
2. **Admin (2)**: Manage members, moderate content
3. **Contributor (3)**: Upload photos, basic management
4. **Viewer (4)**: View all photos, basic access
5. **Restricted Viewer (5)**: Limited viewing access

#### Photo Permissions
- **Upload**: Roles 1, 2, 3
- **View**: Roles 1, 2, 3, 4
- **Delete**: Uploader or Roles 1, 2
- **Tag**: Roles 1, 2, 3

---

## Best Practices

### File Upload Guidelines

1. **Supported Formats**: JPEG, PNG, GIF, WebP
2. **Size Limits**: 
   - Profile pictures: 5MB
   - Photos: 10MB
   - Batch uploads: Max 20 files
3. **File Naming**: UUID-based automatic naming
4. **Storage**: Modular system supports local and cloud storage

### API Usage Recommendations

1. **Pagination**: Use limit/offset for large datasets
2. **Filtering**: Utilize query parameters for efficient data retrieval
3. **Error Handling**: Always check response status codes
4. **Authentication**: Include Bearer token in all requests
5. **Rate Limiting**: Respect API limits (implement as needed)

### Security Considerations

1. **File Validation**: All uploads are validated for type and size
2. **Permission Checks**: Every operation validates user permissions
3. **Input Sanitization**: All inputs are validated and sanitized
4. **SQL Injection Protection**: Using SQLAlchemy ORM
5. **XSS Prevention**: Proper content type handling

---

## Examples

### Complete Photo Upload Workflow

```bash
# 1. Login to get token
TOKEN=$(curl -X POST "http://localhost:8000/auth/supabase_login" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"password123"}' \
  | jq -r '.access_token')

# 2. Create a group
GROUP_ID=$(curl -X POST "http://localhost:8000/groups/supabase_create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Group","description":"My test group"}' \
  | jq -r '.id')

# 3. Upload photo
curl -X POST "http://localhost:8000/photos/supabase_upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "group_id=$GROUP_ID" \
  -F "file=@photo.jpg" \
  -F "tags=test,demo" \
  -F "description=Test photo upload"

# 4. Get group photos
curl -X GET "http://localhost:8000/photos/supabase_group/$GROUP_ID?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Batch Operations Example

```bash
# Tag multiple photos
curl -X POST "http://localhost:8000/photos/supabase_batch_tag" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "photo_ids": [1, 2, 3, 4, 5],
    "tags": ["vacation", "summer", "family"]
  }'
```

---

## API Testing

### Using Postman

1. Import the API collection (create from this documentation)
2. Set up environment variables:
   - `base_url`: http://localhost:8000
   - `token`: {{auth_token}}
3. Use pre-request scripts to handle authentication

### Using Python Requests

```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/supabase_login', 
                        json={'email': 'john@example.com', 'password': 'password123'})
token = response.json()['access_token']

# Upload photo
headers = {'Authorization': f'Bearer {token}'}
files = {'file': open('photo.jpg', 'rb')}
data = {'group_id': 1, 'tags': 'test,photo', 'description': 'Test upload'}
response = requests.post('http://localhost:8000/photos/supabase_upload', 
                        headers=headers, files=files, data=data)
```

---

## Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file size limits
   - Verify file type is supported
   - Ensure proper permissions

2. **Authentication Errors**
   - Verify token is valid and not expired
   - Check Authorization header format
   - Ensure user exists in both local and Supabase

3. **Permission Denied**
   - Check user group membership
   - Verify user role permissions
   - Ensure group exists

4. **Storage Issues**
   - Check STORAGE_TYPE environment variable
   - Verify upload directory exists and is writable
   - For S3: validate AWS credentials

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

This will provide detailed information about:
- Database queries
- File operations
- Supabase synchronization
- Permission checks

---

## Changelog

### Version 1.0.0 (Current)
- Initial release of Supabase integration
- Modular storage system
- Complete API documentation
- Authentication with Supabase
- Advanced analytics and reporting
- Batch operations support

### Planned Features
- Real-time notifications via Supabase
- Advanced face recognition
- Video upload support
- Mobile app integration
- Advanced search capabilities 