"""grant6.py <scripts dir> <repo> <kind>...: record session grant '<kind> **' as sid '<kind>' (state/home from the environment)."""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1]); import judge
for k in sys.argv[3:]:
    judge.record({"session_id": k}, Path(sys.argv[2]), f"{k} ** -- whole repo", "Regent: message")
