"""
Compatibility module.

The repo originally had a misspelled `tranform.py`. `main.py` imports `transform`,
so we re-export the implementation here without breaking existing references.
"""

from tranform import build_features  # noqa: F401


