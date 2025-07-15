#!/bin/bash

echo "🚀 SnapVault Backend Setup for Unix/Linux/macOS"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "✅ Python found"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Create virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "🔄 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "🔄 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

# Create uploads directory
if [ ! -d "uploads" ]; then
    mkdir uploads
    echo "✅ Created uploads directory"
else
    echo "✅ Uploads directory already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "2. Run the application:"
echo "   uvicorn main:app --reload"
echo "3. Access the API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "📚 For more information, see API_DOCUMENTATION.md" 