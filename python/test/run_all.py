#!/usr/bin/env python
from __future__ import print_function
import sys
import unittest

loader = unittest.TestLoader()
loader.testMethodPrefix = "test"
suite1 = loader.discover('.', pattern="init.py")
suite2 = loader.discover('.', pattern="test_*.py")
suite3 = loader.discover('.', pattern="clean.py")
alltests = unittest.TestSuite((suite1, suite2, suite3))
test_result = unittest.TextTestRunner(verbosity=2).run(alltests)

if test_result.wasSuccessful():
    sys.exit()
else:
    number_failed = len(test_result.failures) + len(test_result.errors)
    sys.exit(number_failed)
