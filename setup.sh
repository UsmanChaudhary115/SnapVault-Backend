#!/bin/bash

# Default options
INCLUDE_SUPABASE=false
SUPABASE_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-supabase)
            INCLUDE_SUPABASE=true
            shift
            ;;
        --supabase-only)
            SUPABASE_ONLY=true
            shift
            ;;
        -h|--help)
            echo "SnapVault Backend Setup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-supabase     Include Supabase database setup"
            echo "  --supabase-only     Only run Supabase database setup"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Basic setup"
            echo "  $0 --with-supabase   # Setup with Supabase database"
            echo "  $0 --supabase-only   # Only setup Supabase database"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 SnapVault Backend Setup for Unix/Linux/macOS"
echo "================================================"

# Function to check environment variables
check_env_vars() {
    echo "🔍 Checking environment variables..."
    missing_vars=()
    
    if [ -z "$SUPABASE_URL" ]; then
        missing_vars+=("SUPABASE_URL")
    fi
    
    if [ -z "$SUPABASE_ANON_KEY" ]; then
        missing_vars+=("SUPABASE_ANON_KEY")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "⚠️  Missing environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "   ❌ $var"
        done
        echo ""
        echo "📝 Please set these environment variables for Supabase integration:"
        echo "   export SUPABASE_URL='your-supabase-url'"
        echo "   export SUPABASE_ANON_KEY='your-anon-key'"
        echo "   export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'  # For admin operations"
        return 1
    else
        echo "✅ All required environment variables are set"
        return 0
    fi
}

# Function to setup Supabase database
setup_supabase() {
    echo ""
    echo "🔧 Setting up Supabase database..."
    echo "========================================="
    
    # Check environment variables
    if ! check_env_vars; then
        echo "⚠️  Supabase setup skipped due to missing environment variables"
        return 1
    fi
    
    # Run Supabase setup
    echo "🔄 Setting up Supabase database tables..."
    source venv/bin/activate
    python -m utils.supabase_setup
    if [ $? -ne 0 ]; then
        echo "❌ Supabase database setup failed"
        return 1
    fi
    
    echo "✅ Supabase database setup completed"
    return 0
}

# If supabase-only mode, skip basic setup
if [ "$SUPABASE_ONLY" = true ]; then
    echo "🔧 Supabase-only setup mode"
    echo ""
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Please run basic setup first."
        echo "   ./setup.sh"
        exit 1
    fi
    
    # Setup Supabase
    if setup_supabase; then
        echo ""
        echo "🎉 Supabase database setup completed successfully!"
    else
        echo ""
        echo "❌ Supabase database setup failed"
        exit 1
    fi
    exit 0
fi

# Basic setup steps
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

# Create uploads directories
echo "🔄 Creating upload directories..."
directories=("uploads" "uploads/photos" "uploads/profile_pictures")

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✅ Created $dir directory"
    else
        echo "✅ $dir directory already exists"
    fi
done

# Setup Supabase if requested
if [ "$INCLUDE_SUPABASE" = true ]; then
    if ! setup_supabase; then
        echo "⚠️  Basic setup completed, but Supabase setup failed"
        echo "   You can run Supabase setup later with: ./setup.sh --supabase-only"
    fi
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"

if [ "$INCLUDE_SUPABASE" = false ]; then
    echo "2. (Optional) Setup Supabase database:"
    echo "   ./setup.sh --supabase-only"
    echo "3. Run the application:"
else
    echo "2. Run the application:"
fi

echo "   uvicorn main:app --reload"

if [ "$INCLUDE_SUPABASE" = false ]; then
    echo "4. Access the API documentation:"
else
    echo "3. Access the API documentation:"
fi

echo "   http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   • API_DOCUMENTATION.md - Local routes"
echo "   • SUPABASE_API_DOCUMENTATION.md - Supabase routes"
echo "   • SUPABASE_TEST_CASES.md - Test scenarios" 