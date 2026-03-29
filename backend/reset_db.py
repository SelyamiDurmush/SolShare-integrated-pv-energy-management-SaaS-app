import os
import subprocess
import sys

# 1. Delete the existing database file
if os.path.exists("solshare.db"):
    try:
        os.remove("solshare.db")
        print("✅ Deleted old database (solshare.db)")
    except PermissionError:
        print("❌ Error: Could not delete database. Please stop the running server (CTRL+C) and try again.")
        exit(1)

# 2. Run the seed script to recreate it with new data
subprocess.run([sys.executable, "seed.py"])