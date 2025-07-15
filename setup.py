#!/usr/bin/env python3
"""
SnapVault Backend Setup Script
This script automates the setup process for the SnapVault backend project.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def activate_virtual_environment():
    """Activate virtual environment"""
    if platform.system() == "Windows":
        activate_script = os.path.join("venv", "Scripts", "activate")
        if os.path.exists(activate_script):
            print("✅ Virtual environment activation script found")
            return True
    else:
        activate_script = os.path.join("venv", "bin", "activate")
        if os.path.exists(activate_script):
            print("✅ Virtual environment activation script found")
            return True
    
    print("❌ Virtual environment activation script not found")
    return False

def install_dependencies():
    """Install project dependencies"""
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip.exe")
        python_path = os.path.join("venv", "Scripts", "python.exe")
        # Fallback to non-.exe versions
        if not os.path.exists(pip_path):
            pip_path = os.path.join("venv", "Scripts", "pip")
        if not os.path.exists(python_path):
            python_path = os.path.join("venv", "Scripts", "python")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    if not os.path.exists(pip_path):
        print("❌ pip not found in virtual environment")
        print(f"   Looked for: {pip_path}")
        print("   Try recreating the virtual environment with: python -m venv venv")
        return False
    
    return run_command(f'"{pip_path}" install -r requirements.txt', "Installing dependencies")

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    directories = ["uploads", "uploads/photos", "uploads/profile_pictures"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created {directory} directory")
        else:
            print(f"✅ {directory} directory already exists")
    return True

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing_vars = []
    
    print("🔍 Checking environment variables...")
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   ❌ {var}")
        print("\n📝 Please set these environment variables for Supabase integration:")
        print("   export SUPABASE_URL='your-supabase-url'")
        print("   export SUPABASE_ANON_KEY='your-anon-key'")
        print("   export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'  # For admin operations")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def setup_supabase_database():
    """Setup Supabase database tables"""
    if platform.system() == "Windows":
        python_path = os.path.join("venv", "Scripts", "python.exe")
        # Fallback to non-.exe version
        if not os.path.exists(python_path):
            python_path = os.path.join("venv", "Scripts", "python")
    else:
        python_path = os.path.join("venv", "bin", "python")
    
    print("\n🔧 Setting up Supabase database...")
    print("=" * 40)
    
    # Check if environment variables are set
    if not check_environment_variables():
        print("⚠️  Supabase setup skipped due to missing environment variables")
        return False
    
    # Verify python path exists
    if not os.path.exists(python_path):
        print(f"❌ Python not found in virtual environment: {python_path}")
        print("   Try recreating the virtual environment with: python -m venv venv")
        return False
    
    # Run the Supabase setup script
    try:
        command = f'"{python_path}" -m utils.supabase_setup'
        return run_command(command, "Setting up Supabase database tables")
    except Exception as e:
        print(f"❌ Supabase setup failed: {e}")
        return False

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SnapVault Backend Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Basic setup
  python setup.py --with-supabase    # Setup with Supabase database
  python setup.py --supabase-only    # Only setup Supabase database
        """
    )
    
    parser.add_argument(
        '--with-supabase',
        action='store_true',
        help='Include Supabase database setup'
    )
    
    parser.add_argument(
        '--supabase-only',
        action='store_true',
        help='Only run Supabase database setup (skip basic setup)'
    )
    
    args = parser.parse_args()
    
    print("🚀 SnapVault Backend Setup")
    print("=" * 40)
    
    # If supabase-only, just run Supabase setup
    if args.supabase_only:
        if setup_supabase_database():
            print("\n🎉 Supabase database setup completed successfully!")
        else:
            print("\n❌ Supabase database setup failed")
            sys.exit(1)
        return
    
    # Basic setup steps
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Check virtual environment activation
    if not activate_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create uploads directory
    if not create_uploads_directory():
        sys.exit(1)
    
    # Setup Supabase if requested
    if args.with_supabase:
        if not setup_supabase_database():
            print("⚠️  Basic setup completed, but Supabase setup failed")
            print("   You can run Supabase setup later with: python setup.py --supabase-only")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    if not args.with_supabase and not args.supabase_only:
        print("2. (Optional) Setup Supabase database:")
        print("   python setup.py --supabase-only")
        print("3. Run the application:")
    else:
        print("2. Run the application:")
    
    print("   uvicorn main:app --reload")
    
    if args.with_supabase and not args.supabase_only:
        print("4. Access the API documentation:")
    else:
        print("3. Access the API documentation:")
    
    print("   http://localhost:8000/docs")
    print("\n📚 Documentation:")
    print("   • API_DOCUMENTATION.md - Local routes")
    print("   • SUPABASE_API_DOCUMENTATION.md - Supabase routes")
    print("   • SUPABASE_TEST_CASES.md - Test scenarios")

if __name__ == "__main__":
    main() 