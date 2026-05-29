# conftest.py
def pytest_configure(config):
    # Safely attach a custom attribute to the config object
    config.custom_testbook_prefixes = [
        "### TC-SYS-INT-"
    ]


def pytest_addoption(parser):
    group = parser.getgroup("testbook")

    # Enable PDF flag
    group.addoption(
        "--generate-pdf",
        action="store_true",
        dest="generate_pdf",
        default=True,
        help="Generate PDF report after tests"
    )

    # Disable PDF flag (explicitly defined)
    group.addoption(
        "--no-generate-pdf",
        action="store_false",
        dest="generate_pdf",
        help="Do not generate PDF report after tests"
    )