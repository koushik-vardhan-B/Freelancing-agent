"""
TEST 2: LangGraph Import Check

Run this to verify LangGraph dependencies are installed correctly.

Usage:
    python test_langgraph.py
"""

print("Testing LangGraph imports...")
print("-" * 40)

try:
    import jsonpatch
    print(f"[OK] jsonpatch: {jsonpatch.__version__}")
except ImportError as e:
    print(f"[FAIL] jsonpatch MISSING: {e}")
    print("   Run: pip install jsonpatch")

try:
    from langchain_core.runnables import Runnable
    print("[OK] langchain_core.runnables")
except ImportError as e:
    print(f"[FAIL] langchain_core BROKEN: {e}")
    print("   Run: pip install --upgrade langchain-core")

try:
    from langgraph.graph import StateGraph, END
    print("[OK] langgraph.graph")
except ImportError as e:
    print(f"[FAIL] langgraph MISSING: {e}")
    print("   Run: pip install langgraph")

print("-" * 40)
print("If all checks passed: LangGraph OK!")
