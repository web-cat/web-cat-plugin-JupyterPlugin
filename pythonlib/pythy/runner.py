import sys
import os
import pythy

__import__('instructor_tests', locals(), globals())
with open('_results.json', 'w') as f:
  pythy.runAllTests(f)
