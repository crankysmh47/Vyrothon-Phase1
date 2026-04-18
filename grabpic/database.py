"""
Database module for initializing the Supabase client.
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# Environment variable validation
# OS environment access uses square brackets to enforce fail-fast behavior at startup
SUPABASE_URL: str = os.environ['SUPABASE_URL']
SUPABASE_KEY: str = os.environ['SUPABASE_KEY']

# Initialize singleton Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
