import pytest


@pytest.mark.skip_unless_demo_data_installed
def test_skip_without_demo_rollback_registry(rollback_registry):
    # If Anyblok test case database is setup without `--with-demo` so this
    # test should be skipped otherwise `with-demo` parameter should be True
    assert rollback_registry.System.Parameter.get("with-demo", False) is True, (
        "`--with-demo` is not used to setup database to run AnyBlok tests "
        "so this test is intentionally skipped to validate "
        "skip_unless_demo_data_installed pytest marker behavior"
    )


@pytest.mark.skip_while_demo_data_installed
def test_skip_with_demo_rollback_registry(rollback_registry):
    # If Anyblok test case database is setup with `--with-demo` so this
    # test should be skipped otherwise `with-demo` parameter should be False
    # skip_unless_demo_data_installed marker
    assert rollback_registry.System.Parameter.get(
        "with-demo", False
    ) is False, (
        "`--with-demo` is not used to setup database to run AnyBlok tests "
        "so this test is intentionally skipped to validate "
        "skip_unless_demo_data_installed pytest marker behavior"
    )
