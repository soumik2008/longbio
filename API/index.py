import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from main import app

# Vercel serverless handler
def handler(request, context):
    return app
