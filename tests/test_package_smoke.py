from importlib import resources


def test_public_imports_are_available():
    from prometheus_tornado_instrumentator import Instrumentator, metrics

    assert Instrumentator is not None
    assert metrics is not None


def test_package_declares_pep561_typing_marker():
    assert resources.files("prometheus_tornado_instrumentator").joinpath(
        "py.typed"
    ).is_file()
