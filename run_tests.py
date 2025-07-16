import sys
import unittest
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Discover and run tests
loader = unittest.TestLoader()
suite = loader.discover(start_dir='tests', top_level_dir=os.path.abspath(os.path.join(os.path.dirname(__file__))))

runner = unittest.TextTestRunner()
runner.run(suite)