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
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    if not os.path.exists(pip_path):
        print("❌ pip not found in virtual environment")
        return False
    
    return run_command(f'"{pip_path}" install -r requirements.txt', "Installing dependencies")

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("✅ Created uploads directory")
    else:
        print("✅ Uploads directory already exists")
    return True

def main():
    """Main setup function"""
    print("🚀 SnapVault Backend Setup")
    print("=" * 40)
    
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
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Run the application:")
    print("   uvicorn main:app --reload")
    print("3. Access the API documentation:")
    print("   http://localhost:8000/docs")
    print("\n📚 For more information, see API_DOCUMENTATION.md")

if __name__ == "__main__":
    main() 