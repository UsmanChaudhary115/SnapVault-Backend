# 🚀 Supabase Setup Guide for SnapVault

This guide will help you set up Supabase integration with your SnapVault backend application.

## 📋 Prerequisites

1. **SnapVault Backend** - Local setup completed
2. **Supabase Account** - Create at [supabase.com](https://supabase.com)
3. **Environment Variables** - Supabase credentials configured
4. **Python Environment** - Virtual environment activated

## 🔧 Step 1: Create Supabase Project

1. **Sign up/Login** to [Supabase](https://supabase.com)
2. **Create a new project**:
   - Choose a project name (e.g., "snapvault-backend")
   - Set a database password
   - Select a region close to your users
   - Wait for project setup to complete (~2 minutes)

3. **Get your project credentials**:
   - Go to **Settings** → **API**
   - Copy the following values:
     - `Project URL` (looks like: `https://xyz.supabase.co`)
     - `anon public` key
     - `service_role` key (for admin operations)

## 🔑 Step 2: Configure Environment Variables

### For Linux/macOS:

Add to your `.bashrc`, `.zshrc`, or set temporarily:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key-here"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key-here"
```

### For Windows (Command Prompt):

```cmd
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key-here
set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### For Windows (PowerShell):

```powershell
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_ANON_KEY="your-anon-key-here"
$env:SUPABASE_SERVICE_ROLE_KEY="your-service-role-key-here"
```

### Using .env file (Recommended):

Create a `.env` file in your project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

**Note**: Add `.env` to your `.gitignore` to keep credentials secure!

## 🏗️ Step 3: Run Database Setup

### Option A: Automatic Setup (Recommended)

```bash
# For new installations with Supabase
python setup.py --with-supabase

# For existing installations, add Supabase only
python setup.py --supabase-only
```

**OR using shell scripts:**

```bash
# Linux/macOS
./setup.sh --with-supabase
./setup.sh --supabase-only

# Windows
setup.bat --with-supabase
setup.bat --supabase-only
```

### Option B: Manual Setup

```bash
# Activate your virtual environment first
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Run the Supabase setup script
python -m utils.supabase_setup
```

### Option C: Manual Verification

```bash
# Check if tables exist without creating them
python -m utils.supabase_setup --verify-only
```

## 📊 Step 4: Verify Setup

The setup script will create these tables in your Supabase database:

### 📸 **photos** table
- Stores photo metadata and file references
- Links to local storage or S3 buckets
- Includes JSONB metadata for tags, descriptions, etc.

### 👥 **groups** table  
- Group information and invite codes
- Creator tracking and timestamps
- Syncs with local group data

### 👤 **group_members** table
- User-group relationships
- Role-based permissions (5 levels)
- Join timestamps and updates

### 👨‍💼 **user_profiles** table
- Extended user metadata from Supabase Auth
- Links Supabase Auth users to local user records
- Profile pictures, bios, and provider information

## 🔒 Step 5: Configure Authentication (Optional)

### Enable Google OAuth:

1. Go to **Authentication** → **Providers** in Supabase
2. Enable **Google** provider
3. Add your Google OAuth credentials:
   - Get credentials from [Google Cloud Console](https://console.cloud.google.com)
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs

### Set up Row Level Security (RLS):

The setup script automatically enables RLS. You can customize policies in Supabase:

1. Go to **Authentication** → **Policies**
2. Create custom policies for your use case
3. Test with the built-in policy editor

## ✅ Step 6: Test Your Setup

### Test Basic Connectivity:

```bash
python -c "
from utils.supabase_client import get_supabase_client
client = get_supabase_client()
result = client.table('photos').select('*').limit(1).execute()
print('✅ Supabase connection successful!')
"
```

### Test API Endpoints:

1. **Start your application**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Visit the API documentation**:
   - http://localhost:8000/docs
   - Look for endpoints with `supabase_` prefix

3. **Try a Supabase endpoint**:
   ```bash
   # Register a new user via Supabase
   curl -X POST "http://localhost:8000/auth/supabase_register" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "name=Test User&email=test@example.com&password=testpassword123"
   ```

## 🎯 Available Supabase Endpoints

After setup, you'll have access to **31 Supabase endpoints**:

### 🔐 Authentication (7 endpoints)
- Google OAuth login and callback
- Registration (simple and with profile picture)
- Login with Supabase auth
- Account deletion

### 👤 User Management (7 endpoints)
- Profile management
- Bio and name updates
- Profile picture uploads
- Email updates
- Storage statistics
- User activity tracking
- Account deletion

### 👥 Group Management (9 endpoints)
- Group creation and updates
- Join groups with invite codes
- Member management with roles
- Group analytics and statistics
- Ownership transfers
- Group deletion

### 📸 Photo Management (8 endpoints)
- Single and batch photo uploads
- Advanced filtering and search
- Photo analytics
- Batch tagging operations
- Photo deletion and management

## 🛠️ Troubleshooting

### Common Issues:

**1. "Failed to connect to Supabase"**
- ✅ Check environment variables are set correctly
- ✅ Verify your Supabase URL and keys
- ✅ Ensure your Supabase project is active

**2. "Table does not exist"**
- ✅ Run the setup script: `python -m utils.supabase_setup`
- ✅ Check the Supabase dashboard for created tables
- ✅ Verify your service role key has admin permissions

**3. "RLS policy violations"**
- ✅ Check Row Level Security policies in Supabase
- ✅ Ensure your user has proper permissions
- ✅ Test with RLS disabled temporarily

**4. "Environment variables not found"**
- ✅ Restart your terminal after setting variables
- ✅ Use `echo $SUPABASE_URL` (Linux/macOS) or `echo %SUPABASE_URL%` (Windows) to verify
- ✅ Check for typos in variable names

### Debug Mode:

Run setup with detailed output:

```bash
python -m utils.supabase_setup --json-output
```

### Reset Database:

If you need to start over:

1. Go to Supabase Dashboard → **SQL Editor**
2. Run: 
   ```sql
   DROP TABLE IF EXISTS photos CASCADE;
   DROP TABLE IF EXISTS groups CASCADE;
   DROP TABLE IF EXISTS group_members CASCADE;
   DROP TABLE IF EXISTS user_profiles CASCADE;
   ```
3. Re-run setup script

## 📚 Additional Resources

- **[Supabase Documentation](https://supabase.com/docs)**
- **[SnapVault API Documentation](./SUPABASE_API_DOCUMENTATION.md)**
- **[Test Cases](./SUPABASE_TEST_CASES.md)**
- **[Supabase Dashboard](https://supabase.com/dashboard)**

## 🔄 Migration Path to S3

Your setup is already prepared for S3 migration:

1. The modular storage system in `utils/storage.py` supports S3
2. File URLs are generated dynamically
3. Simply change `STORAGE_TYPE=s3` in environment variables
4. Add S3 credentials when ready to migrate

---

## 🎉 You're Ready!

Once setup is complete, you have:

- ✅ **Dual-database architecture** (Local + Supabase)
- ✅ **31 Supabase-integrated endpoints**
- ✅ **Google OAuth authentication**
- ✅ **File storage with S3-ready architecture**
- ✅ **Professional error handling and logging**
- ✅ **Comprehensive documentation and testing**

Your SnapVault backend now supports both local and Supabase operations seamlessly!

---

**Need help?** Check the troubleshooting section above or review the documentation files for more details. 