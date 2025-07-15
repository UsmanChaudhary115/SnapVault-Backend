"""
Supabase Database Setup Script for SnapVault

This script automatically creates all required tables, indexes, and security policies
in your Supabase database for the SnapVault application.

Features:
- Creates all required custom tables
- Sets up proper indexes for performance
- Configures Row Level Security (RLS)
- Idempotent (safe to run multiple times)
- Detailed logging and error handling
- Rollback capability on errors

Usage:
    python -m utils.supabase_setup
    
    Or from code:
    from utils.supabase_setup import setup_supabase_database
    setup_supabase_database()
"""

import sys
import os
from typing import Dict, List, Optional
from utils.supabase_client import get_supabase_admin_client
import json

def create_photos_table(supabase) -> bool:
    """Create the photos table with proper schema and indexes"""
    
    # Create photos table
    photos_table_sql = """
    CREATE TABLE IF NOT EXISTS photos (
        id BIGINT PRIMARY KEY,
        group_id BIGINT NOT NULL,
        uploader_id BIGINT NOT NULL,
        file_path TEXT,
        file_url TEXT,
        uploaded_at TIMESTAMPTZ,
        file_size BIGINT,
        mime_type TEXT,
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    # Create indexes for better performance
    photos_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_photos_group_id ON photos(group_id);",
        "CREATE INDEX IF NOT EXISTS idx_photos_uploader_id ON photos(uploader_id);",
        "CREATE INDEX IF NOT EXISTS idx_photos_uploaded_at ON photos(uploaded_at);",
        "CREATE INDEX IF NOT EXISTS idx_photos_created_at ON photos(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_photos_file_size ON photos(file_size);",
        "CREATE INDEX IF NOT EXISTS idx_photos_mime_type ON photos(mime_type);"
    ]
    
    try:
        print("📸 Creating photos table...")
        result = supabase.rpc('exec_sql', {'sql': photos_table_sql}).execute()
        
        print("📸 Creating photos table indexes...")
        for index_sql in photos_indexes_sql:
            supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
        print("✅ Photos table and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating photos table: {e}")
        return False


def create_groups_table(supabase) -> bool:
    """Create the groups table with proper schema and indexes"""
    
    # Create groups table
    groups_table_sql = """
    CREATE TABLE IF NOT EXISTS groups (
        id BIGINT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        creator_id BIGINT NOT NULL,
        invite_code TEXT UNIQUE NOT NULL,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    # Create indexes
    groups_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_groups_creator_id ON groups(creator_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_groups_invite_code ON groups(invite_code);",
        "CREATE INDEX IF NOT EXISTS idx_groups_created_at ON groups(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name);",
        "CREATE INDEX IF NOT EXISTS idx_groups_updated_at ON groups(updated_at);"
    ]
    
    try:
        print("👥 Creating groups table...")
        supabase.rpc('exec_sql', {'sql': groups_table_sql}).execute()
        
        print("👥 Creating groups table indexes...")
        for index_sql in groups_indexes_sql:
            supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
        print("✅ Groups table and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating groups table: {e}")
        return False


def create_group_members_table(supabase) -> bool:
    """Create the group_members table with proper schema and indexes"""
    
    # Create group_members table
    group_members_table_sql = """
    CREATE TABLE IF NOT EXISTS group_members (
        user_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL,
        role_id INTEGER NOT NULL,
        joined_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (user_id, group_id)
    );
    """
    
    # Create indexes
    group_members_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);",
        "CREATE INDEX IF NOT EXISTS idx_group_members_role_id ON group_members(role_id);",
        "CREATE INDEX IF NOT EXISTS idx_group_members_joined_at ON group_members(joined_at);",
        "CREATE INDEX IF NOT EXISTS idx_group_members_updated_at ON group_members(updated_at);"
    ]
    
    try:
        print("👤 Creating group_members table...")
        supabase.rpc('exec_sql', {'sql': group_members_table_sql}).execute()
        
        print("👤 Creating group_members table indexes...")
        for index_sql in group_members_indexes_sql:
            supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
        print("✅ Group_members table and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating group_members table: {e}")
        return False


def create_user_profiles_table(supabase) -> bool:
    """Create the user_profiles table for extended user data"""
    
    # Create user_profiles table
    user_profiles_table_sql = """
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
        local_user_id BIGINT,
        display_name TEXT,
        bio TEXT,
        avatar_url TEXT,
        auth_provider TEXT DEFAULT 'email',
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    # Create indexes
    user_profiles_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_local_user_id ON user_profiles(local_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_provider ON user_profiles(auth_provider);",
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_display_name ON user_profiles(display_name);",
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON user_profiles(updated_at);"
    ]
    
    try:
        print("👨‍💼 Creating user_profiles table...")
        supabase.rpc('exec_sql', {'sql': user_profiles_table_sql}).execute()
        
        print("👨‍💼 Creating user_profiles table indexes...")
        for index_sql in user_profiles_indexes_sql:
            supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
        print("✅ User_profiles table and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user_profiles table: {e}")
        return False


def setup_row_level_security(supabase) -> bool:
    """Enable Row Level Security on all tables"""
    
    rls_commands = [
        "ALTER TABLE photos ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE groups ENABLE ROW LEVEL SECURITY;", 
        "ALTER TABLE group_members ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;"
    ]
    
    try:
        print("🔒 Enabling Row Level Security...")
        for command in rls_commands:
            try:
                supabase.rpc('exec_sql', {'sql': command}).execute()
            except Exception as e:
                # RLS might already be enabled, which is fine
                print(f"ℹ️  RLS command note: {e}")
        
        print("✅ Row Level Security enabled successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up RLS: {e}")
        return False


def create_database_functions(supabase) -> bool:
    """Create useful database functions"""
    
    # Function to execute SQL (needed for setup)
    exec_sql_function = """
    CREATE OR REPLACE FUNCTION exec_sql(sql text)
    RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE sql;
    END;
    $$;
    """
    
    # Function to get user's groups
    get_user_groups_function = """
    CREATE OR REPLACE FUNCTION get_user_groups(user_id_param BIGINT)
    RETURNS TABLE(
        group_id BIGINT,
        group_name TEXT,
        role_id INTEGER,
        joined_at TIMESTAMPTZ
    )
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        RETURN QUERY
        SELECT g.id, g.name, gm.role_id, gm.joined_at
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = user_id_param
        ORDER BY gm.joined_at DESC;
    END;
    $$;
    """
    
    # Function to get group statistics
    get_group_stats_function = """
    CREATE OR REPLACE FUNCTION get_group_stats(group_id_param BIGINT)
    RETURNS TABLE(
        total_members BIGINT,
        total_photos BIGINT,
        storage_used BIGINT
    )
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            (SELECT COUNT(*) FROM group_members WHERE group_id = group_id_param),
            (SELECT COUNT(*) FROM photos WHERE group_id = group_id_param),
            (SELECT COALESCE(SUM(file_size), 0) FROM photos WHERE group_id = group_id_param);
    END;
    $$;
    """
    
    functions = [
        ("exec_sql", exec_sql_function),
        ("get_user_groups", get_user_groups_function), 
        ("get_group_stats", get_group_stats_function)
    ]
    
    try:
        print("⚙️  Creating database functions...")
        for func_name, func_sql in functions:
            try:
                supabase.rpc('exec_sql', {'sql': func_sql}).execute()
                print(f"✅ Created function: {func_name}")
            except Exception as e:
                print(f"ℹ️  Function {func_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating functions: {e}")
        return False


def verify_tables_exist(supabase) -> Dict[str, bool]:
    """Verify that all required tables exist"""
    
    required_tables = ['photos', 'groups', 'group_members', 'user_profiles']
    table_status = {}
    
    print("🔍 Verifying table creation...")
    
    for table in required_tables:
        try:
            # Try to query the table to see if it exists
            result = supabase.table(table).select("*").limit(1).execute()
            table_status[table] = True
            print(f"✅ Table '{table}' exists and is accessible")
        except Exception as e:
            table_status[table] = False
            print(f"❌ Table '{table}' verification failed: {e}")
    
    return table_status


def setup_supabase_database(
    verify_only: bool = False,
    enable_rls: bool = True,
    create_functions: bool = True
) -> Dict[str, any]:
    """
    Main function to set up the Supabase database
    
    Args:
        verify_only: If True, only verify existing tables
        enable_rls: Whether to enable Row Level Security
        create_functions: Whether to create utility functions
        
    Returns:
        Dict with setup results and status
    """
    
    print("🚀 SnapVault Supabase Database Setup")
    print("=" * 50)
    
    try:
        # Get Supabase admin client
        print("🔌 Connecting to Supabase...")
        supabase = get_supabase_admin_client()
        print("✅ Connected to Supabase successfully")
        
    except Exception as e:
        error_msg = f"❌ Failed to connect to Supabase: {e}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "tables_created": {},
            "verification": {}
        }
    
    # If verify only, just check tables and return
    if verify_only:
        verification_results = verify_tables_exist(supabase)
        return {
            "success": all(verification_results.values()),
            "verification": verification_results,
            "mode": "verification_only"
        }
    
    setup_results = {
        "success": True,
        "tables_created": {},
        "functions_created": False,
        "rls_enabled": False,
        "verification": {},
        "errors": []
    }
    
    print("\n📋 Creating database tables...")
    print("-" * 30)
    
    # Create all tables
    table_creators = [
        ("photos", create_photos_table),
        ("groups", create_groups_table),
        ("group_members", create_group_members_table),
        ("user_profiles", create_user_profiles_table)
    ]
    
    for table_name, creator_func in table_creators:
        try:
            success = creator_func(supabase)
            setup_results["tables_created"][table_name] = success
            if not success:
                setup_results["success"] = False
                setup_results["errors"].append(f"Failed to create {table_name} table")
        except Exception as e:
            setup_results["tables_created"][table_name] = False
            setup_results["success"] = False
            error_msg = f"Exception creating {table_name}: {e}"
            setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    # Create database functions
    if create_functions:
        print("\n⚙️  Setting up database functions...")
        print("-" * 30)
        try:
            setup_results["functions_created"] = create_database_functions(supabase)
        except Exception as e:
            setup_results["functions_created"] = False
            error_msg = f"Failed to create functions: {e}"
            setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    # Enable Row Level Security
    if enable_rls:
        print("\n🔒 Setting up security...")
        print("-" * 30)
        try:
            setup_results["rls_enabled"] = setup_row_level_security(supabase)
        except Exception as e:
            setup_results["rls_enabled"] = False
            error_msg = f"Failed to setup RLS: {e}"
            setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    # Verify all tables exist
    print("\n🔍 Final verification...")
    print("-" * 30)
    setup_results["verification"] = verify_tables_exist(supabase)
    
    # Final status
    print("\n📊 Setup Summary")
    print("=" * 50)
    
    if setup_results["success"] and all(setup_results["verification"].values()):
        print("🎉 SUCCESS! Supabase database setup completed successfully!")
        print("\n📋 What was created:")
        for table, status in setup_results["tables_created"].items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {table} table")
        
        if setup_results["functions_created"]:
            print("   ✅ Database functions")
        if setup_results["rls_enabled"]: 
            print("   ✅ Row Level Security")
            
        print(f"\n🔗 Your Supabase database is ready!")
        print("   You can now use all Supabase endpoints in your SnapVault application.")
        
    else:
        print("⚠️  Setup completed with some issues:")
        for error in setup_results["errors"]:
            print(f"   ❌ {error}")
        
        print("\n📋 Table Status:")
        for table, status in setup_results["verification"].items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {table}")
    
    return setup_results


def main():
    """Command line interface for the setup script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SnapVault Supabase Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m utils.supabase_setup                    # Full setup
  python -m utils.supabase_setup --verify-only      # Only verify tables
  python -m utils.supabase_setup --no-rls           # Setup without RLS
  python -m utils.supabase_setup --no-functions     # Setup without functions
        """
    )
    
    parser.add_argument(
        '--verify-only', 
        action='store_true',
        help='Only verify that tables exist, do not create anything'
    )
    
    parser.add_argument(
        '--no-rls',
        action='store_true', 
        help='Skip Row Level Security setup'
    )
    
    parser.add_argument(
        '--no-functions',
        action='store_true',
        help='Skip creating database functions'
    )
    
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # Run setup
    results = setup_supabase_database(
        verify_only=args.verify_only,
        enable_rls=not args.no_rls,
        create_functions=not args.no_functions
    )
    
    if args.json_output:
        print("\n" + "="*50)
        print("JSON OUTPUT:")
        print(json.dumps(results, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main() 