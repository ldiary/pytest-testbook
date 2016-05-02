"""Pytest-Testbook pytest hooks."""


def pytest_testbook_kernel_setup(scenario):
    """Will be called after the Jupyter kernel is started."""


def pytest_testbook_kernel_teardown(scenario):
    """Will be called before the Jupyter kernel is shut down."""
