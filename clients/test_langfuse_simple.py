#!/usr/bin/env python3
"""Simple Langfuse connection test"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from langfuse import Langfuse

# Initialize client
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

print("✅ Langfuse client initialized")
print(f"   Host: {os.getenv('LANGFUSE_HOST')}")

# Test creating a score (simplest operation)
try:
    langfuse.create_score(
        name="test-score",
        value=1.0,
        trace_id="test-trace-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        comment="Test score from smoke test"
    )
    print("✅ Score created successfully")
    
    # Flush to ensure it's sent
    langfuse.flush()
    print("✅ Data flushed to Langfuse")
    
    print("\n✅ Langfuse is working! Check the UI for the test score.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
finally:
    langfuse.shutdown()
    print("✅ Client shutdown complete")