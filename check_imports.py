import os
import sys
import importlib

# Get all python files in current directory
py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'check_imports.py']

for f in py_files:
    mod_name = f[:-3]
    try:
        importlib.import_module(mod_name)
    except Exception as e:
        print(f"Error importing {mod_name}: {type(e).__name__}: {e}")
