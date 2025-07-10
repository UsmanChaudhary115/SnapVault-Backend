# 📸 SnapVault Backend

SnapVault is a smart photo-sharing platform that leverages **facial recognition** to organize and share photos among group members automatically.

This repository contains the **FastAPI**-powered backend that handles authentication, group management, face embedding, and smart media sharing logic.

---

## 🚀 Features

- ✅ User Registration & Login (JWT-based Auth)
- 🔐 Password Update and Profile Management
- 👥 Group Creation, Joining, and Membership Control
- 🧠 Face Embedding Storage & Matching (via InsightFace)
- 🖼️ Smart Photo Sharing by Recognized Faces
- 📩 Invite-based Group Joining (Unique Code)
- 📞 Clean API design with auto docs (`/docs` via Swagger UI)

---

## ⚒️ Tech Stack

| Layer        | Tech                   |
| ------------ | ---------------------- |
| Backend      | FastAPI (Python 3.10+) |
| Database     | SQLite / PostgreSQL    |
| ORM          | SQLAlchemy             |
| Auth         | JWT + OAuth2 Password  |
| Facial Recog | InsightFace (planned)  |

---

## 📁 Project Structure

```bash
SnapVault-Backend/
│
├── main.py                   # FastAPI entry point
├── database.py               # DB setup and session
│
├── models/                   # SQLAlchemy models
│   ├── user.py
│   ├── group.py
│   ├── group_member.py
│   └── photo.py
│
├── schemas/                  # Pydantic models
│   ├── user.py
│   ├── group.py
│   └── photo.py
│
├── routes/                   # API endpoints
│   ├── auth.py
│   ├── group.py
│   ├── photo.py
│   └── testing.py            # ⚠️ Only for testing, not for production/dev
│
├── utils/                    # Utility functions
│   ├── hash.py               # Password hashing
│   ├── jwt.py                # Token generation
│   └── auth_utils.py         # Auth middleware
│
└── README.md
```

> ⚠️ **Note:**\
> `routes/testing.py` is for internal testing only and **should not be included** in production or active development deployments.

---

## 🔧 Environment Setup

### 1. Clone the repo

```bash
git clone https://github.com/UsmanChaudhary115/SnapVault-Backend.git
cd SnapVault-Backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate     # Windows  
source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Tip:** If `requirements.txt` is missing:

```bash
pip install fastapi uvicorn sqlalchemy pydantic passlib[bcrypt] python-jose[cryptography]
```

### 4. Run the app

```bash
uvicorn main:app --reload
```

---

## 🔑 Auth & Swagger UI

- Visit `http://127.0.0.1:8000/docs`
- Click `Authorize` 🔐 and paste your Bearer token from `/auth/login` response
- Now you can test protected endpoints easily

---

## 📬 API Endpoints

### 🔐 Auth
| Method | Endpoint                       | Description        |
|--------|--------------------------------|--------------------|
| PUT    | `/auth/bio/{updatedBio}`       | Update Bio         |
| GET    | `/auth/me`                     | Read Current User  |
| POST   | `/auth/register`               | Register           |
| POST   | `/auth/login`                  | Login              |
| PUT    | `/auth/update-password`        | Update Password    |

### 👥 Groups
| Method | Endpoint                       | Description         |
|--------|--------------------------------|---------------------|
| POST   | `/groups/create`               | Create Group        |
| POST   | `/groups/join`                 | Join Group          |
| GET    | `/groups/my`                   | Get My Groups       |
| GET    | `/groups/{id}`                 | Get Group           |
| DELETE | `/groups/{id}`                 | Delete Group        |
| PUT    | `/groups/{id}`                 | Update Group        |
| GET    | `/groups/{id}/members`         | Get Group Members   |
| DELETE | `/groups/{id}/leave`           | Leave Group         |

### 🖼️ Photos
| Method | Endpoint                        | Description         |
|--------|----------------------------------|---------------------|
| POST   | `/photos/upload`                | Upload Photo        |
| GET    | `/photos/group/{group_id}`      | Get Group Photos    |
| GET    | `/photos/{photo_id}`            | Get Photo           |

### 🧪 Testing (for dev only)
| Method | Endpoint                        | Description         |
|--------|----------------------------------|---------------------|
| GET    | `/testingallGroups`             | Get All Groups      |
| GET    | `/testing/allAppUsers`          | Get All Users       |

### 🌐 Default
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/`      | Root        |

---

## 🧠 Future Enhancements

- ✅ Face embedding via InsightFace
- 📱 Frontend Integration (React Native)
- 📜 Admin dashboard (Future scope)
- 🔄 WhatsApp + SMS fallback system (Future scope)

---

## 👥 Contributors

- **Muhmmad Waleed** (Backend Developer)
- **Usman Ali** (Backend Developer)

