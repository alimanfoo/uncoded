import uncoded


def test_import():
    assert uncoded is not None


def test_version_is_exposed():
    assert isinstance(uncoded.__version__, str)
    assert uncoded.__version__
