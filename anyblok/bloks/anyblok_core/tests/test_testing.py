import pytest


@pytest.mark.skip_unless_demo_data_installed
def test_skip_rollback_registry(rollback_registry):
    # Anyblok test case database is setup without --with-demo so this
    # test should be skipped in order to validate and honor
    # skip_unless_demo_data_installed marker
    raise Exception(
        "`--with-demo` is not used to setup database to run AnyBlok tests "
        "so this test is intentionally skipped to validate "
        "skip_unless_demo_data_installed pytest marker behavior"
    )
