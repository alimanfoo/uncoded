import uncoded


def test_version_is_non_empty():
    assert isinstance(uncoded.__version__, str)
    assert uncoded.__version__
