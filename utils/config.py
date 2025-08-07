import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# JWT Configuration (for backward compatibility)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "snapvault-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Validate required environment variables
# if not SUPABASE_URL or not SUPABASE_ANON_KEY:
#     raise ValueError("Supabase URL and ANON_KEY must be provided in environment variables")