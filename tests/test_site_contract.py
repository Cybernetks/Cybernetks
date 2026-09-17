"""Discover site suites without colliding with Python's built-in site module."""


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromNames(
        ["tests.site.test_site_contract", "tests.site.test_legacy_routes"]
    )
