import sys
import os

# Add the apps/api-gateway and packages/shared-py to path
current_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(root_dir, "apps", "api-gateway"))
sys.path.append(os.path.join(root_dir, "packages", "shared-py"))

from app.main import app

# Vercel entry point
handler = app
