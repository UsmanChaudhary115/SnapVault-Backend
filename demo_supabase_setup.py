#!/usr/bin/env python3
"""
SnapVault Supabase Setup Demo

This script demonstrates how to use the Supabase setup utilities programmatically
and provides examples of testing the setup.

Usage:
    python demo_supabase_setup.py
"""

import os
import sys
from utils.supabase_setup import setup_supabase_database

def main():
    """Demo the Supabase setup process"""
    print("🚀 SnapVault Supabase Setup Demo")
    print("=" * 50)
    
    # Check if environment variables are set
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n📝 Please set these variables first:")
        print("   export SUPABASE_URL='your-supabase-url'")
        print("   export SUPABASE_ANON_KEY='your-anon-key'")
        print("   export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        return
    
    print("✅ Environment variables are set")
    print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL')[:30]}...")
    print(f"   SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')[:20]}...")
    
    # Demo 1: Verify existing setup
    print("\n🔍 Demo 1: Verify existing tables")
    print("-" * 30)
    verify_results = setup_supabase_database(verify_only=True)
    
    if verify_results["success"]:
        print("✅ All tables exist and are accessible")
    else:
        print("⚠️  Some tables are missing or inaccessible")
        print("\n🔧 Demo 2: Create missing tables")
        print("-" * 30)
        
        # Demo 2: Full setup
        setup_results = setup_supabase_database(
            verify_only=False,
            enable_rls=True,
            create_functions=True
        )
        
        if setup_results["success"]:
            print("✅ Setup completed successfully!")
        else:
            print("❌ Setup failed:")
            for error in setup_results.get("errors", []):
                print(f"   • {error}")
            return
    
    # Demo 3: Test basic connectivity
    print("\n🔌 Demo 3: Test Supabase connectivity")
    print("-" * 30)
    
    try:
        from utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Test each table
        tables = ["photos", "groups", "group_members", "user_profiles"]
        for table in tables:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} table: Accessible")
            except Exception as e:
                print(f"❌ {table} table: {e}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Demo 4: Show setup options
    print("\n⚙️  Demo 4: Available setup options")
    print("-" * 30)
    print("You can run setup with different options:")
    print("")
    print("1. Verify only (no changes):")
    print("   from utils.supabase_setup import setup_supabase_database")
    print("   setup_supabase_database(verify_only=True)")
    print("")
    print("2. Full setup with RLS:")
    print("   setup_supabase_database(enable_rls=True)")
    print("")
    print("3. Setup without functions:")
    print("   setup_supabase_database(create_functions=False)")
    print("")
    print("4. Command line usage:")
    print("   python -m utils.supabase_setup")
    print("   python -m utils.supabase_setup --verify-only")
    print("   python -m utils.supabase_setup --no-rls")
    
    # Demo 5: Show next steps
    print("\n🎯 Demo 5: Next steps")
    print("-" * 30)
    print("Your Supabase database is ready! You can now:")
    print("")
    print("1. Start your SnapVault application:")
    print("   uvicorn main:app --reload")
    print("")
    print("2. Visit the API documentation:")
    print("   http://localhost:8000/docs")
    print("")
    print("3. Look for endpoints with 'supabase_' prefix")
    print("")
    print("4. Test authentication:")
    print("   POST /auth/supabase_register")
    print("   POST /auth/supabase_login")
    print("")
    print("5. Try photo operations:")
    print("   POST /photo/supabase_upload")
    print("   GET /photo/supabase_group/{group_id}")
    print("")
    print("6. Manage groups:")
    print("   POST /group/supabase_create")
    print("   POST /group/supabase_join")
    
    print("\n🎉 Demo completed successfully!")
    print("Check SUPABASE_SETUP_GUIDE.md for detailed instructions.")

if __name__ == "__main__":
    main() 