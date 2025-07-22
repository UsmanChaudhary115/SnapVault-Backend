from supabase import create_client, Client
from typing import Optional
from .config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
from .config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# Create Supabase clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_supabase_client() -> Client:
    """Get the Supabase client for user operations"""
    return supabase

def get_supabase_admin_client() -> Client:
    """Get the Supabase admin client for admin operations"""
    return supabase_admin

def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Verify a Supabase JWT token and return user data
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Verify the token using Supabase
        response = supabase.auth.get_user(token)
        if response.user:
            return {
                "sub": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata
            }
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def create_supabase_user(email: str, password: str, user_data: dict = None) -> dict:
    """
    Create a new user in Supabase
    """
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": user_data or {}
            }
        })
        return response
    except Exception as e:
        raise Exception(f"Failed to create Supabase user: {e}")

def sign_in_with_password(email: str, password: str) -> dict:
    """
    Sign in user with email and password
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        raise Exception(f"Failed to sign in: {e}")

def get_google_oauth_url(redirect_url: str) -> str:
    """
    Get Google OAuth URL for authentication
    """
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        return response.url
    except Exception as e:
        raise Exception(f"Failed to get Google OAuth URL: {e}") 