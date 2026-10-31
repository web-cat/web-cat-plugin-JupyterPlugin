"""
Main entry point for running instructor tests against student submissions.
"""

import sys
import os
import json
import traceback
import pythy

def main():
    try:
        import instructor_tests
    except Exception as e:
        exctype, val, tb = sys.exc_info()
        err_msg = f"{exctype.__name__}: {str(val)}"
        frames = traceback.format_exception(exctype, val, tb)
        filtered = [f.strip() for f in frames if 'pythy/runner' not in f]
        result = {
            'categories': ['Execution Error'],
            'tests': [{
                'name': 'TestImportError',
                'description': 'Error loading test suite or student code',
                'points': 0,
                'result': 'error',
                'exception': exctype.__name__,
                'reason': err_msg,
                'traceback': filtered
            }],
            'output': ''
        }
        with open('_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4)
        sys.exit(1)

    with open('_results.json', 'w', encoding='utf-8') as f:
        pythy.runAllTests(f)

if __name__ == '__main__':
    main()
