# Testing Framework for VTP Lithophane

This directory contains tests for the VTP Lithophane project. The tests are organized into the following structure:

```
tests/
│
├── __init__.py             # Makes the tests directory a package
├── manual_test_template.py # Manual testing script for templates
│
├── unit/                   # Unit tests directory
│   ├── __init__.py         # Makes the unit directory a package
│   ├── test_gcode_generator.py  # Tests for G-code generation with templates
│   ├── test_parameters.py       # Tests for PrintParameters class
│   └── test_template_handler.py # Tests for GcodeTemplateHandler class
│
└── integration/            # Integration tests directory
    ├── __init__.py         # Makes the integration directory a package
    └── test_template_integration.py # Tests for template integration with G-code generation
```

## Running Tests

You can run the tests using the `run_tests.py` script in the project root:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run a specific test file
python run_tests.py tests/unit/test_template_handler.py

# Run tests in a specific directory
python run_tests.py tests/unit

# Run with increased verbosity
python run_tests.py --verbose
```

## Adding New Tests

To add new tests:

1. For unit tests, create a new Python file in the `tests/unit/` directory with a name starting with `test_`.
2. For integration tests, create a new Python file in the `tests/integration/` directory with a name starting with `test_`.
3. Ensure your test files import the necessary modules and follow the `unittest` framework conventions.

## Test Conventions

- Unit tests should test individual components in isolation
- Integration tests should test the interaction between components
- All test files should include proper docstrings
- Test methods should have descriptive names
- Test failures should provide clear error messages

## Dependencies

The tests rely on the Python `unittest` framework, which is included in the standard library.

## Continuous Integration

These tests can be integrated into a CI/CD pipeline to ensure code quality and prevent regressions.
