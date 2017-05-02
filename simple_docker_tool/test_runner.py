#!/usr/bin/python

import logging.config
import unittest

from tests import test_container_manager

__author__ = 'Nikitas Papangelopoulos'

"""
A simple script to run all tests.
"""

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

suite = unittest.TestSuite()

suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_container_manager))

unittest.TextTestRunner().run(suite)
