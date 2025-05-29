#!/usr/bin/env python
"""
Test runner for VTP Lithophane tests.
"""
import argparse
import os
import sys
import unittest
from pathlib import Path

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def run_all_tests():
    """Run all test cases."""
    # Discover and run all tests
    print("Running all tests...")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1


def run_unit_tests():
    """Run only unit tests."""
    # Discover and run unit tests
    print("Running unit tests...")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/unit', pattern='test_*.py')

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1


def run_integration_tests():
    """Run only integration tests."""
    # Discover and run integration tests
    print("Running integration tests...")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/integration', pattern='test_*.py')

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_path):
    """Run a specific test file or test case."""
    print(f"Running specific test: {test_path}")

    if not os.path.exists(test_path):
        print(f"Error: Test file '{test_path}' not found")
        return 1

    # If it's a directory, discover tests within it
    if os.path.isdir(test_path):
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover(test_path, pattern='test_*.py')
    else:
        # If it's a file, load the tests from it
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover(os.path.dirname(test_path),
                                          pattern=os.path.basename(test_path))

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run VTP Lithophane tests")
    parser.add_argument('test_type', nargs='?', default='all',
                        help="Test type to run: 'all', 'unit', 'integration', or a specific test path")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Increase output verbosity")

    args = parser.parse_args()

    # Set verbosity level
    if args.verbose:
        os.environ['VTP_TEST_VERBOSE'] = '1'

    # Run tests based on the specified type
    if args.test_type == 'all':
        sys.exit(run_all_tests())
    elif args.test_type == 'unit':
        sys.exit(run_unit_tests())
    elif args.test_type == 'integration':
        sys.exit(run_integration_tests())
    else:
        # Assume it's a path to a specific test file or directory
        sys.exit(run_specific_test(args.test_type))
