import unittest

import ctxcore


class VersionTestCase(unittest.TestCase):
    """Version tests."""

    def test_version(self) -> None:
        """Check ctxcore exposes a version attribute."""
        assert hasattr(ctxcore, "__version__")
        assert isinstance(ctxcore.__version__, str)


if __name__ == "__main__":
    unittest.main()
