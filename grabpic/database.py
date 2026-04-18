import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# We use os.environ[] with square brackets to ensure the app crashes 
# immediately at startup if critical environment variables are missing.
SUPABASE_URL: str = os.environ['SUPABASE_URL']
SUPABASE_KEY: str = os.environ['SUPABASE_KEY']

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
