import unittest

import pycistarget_core


class VersionTestCase(unittest.TestCase):
    """Version tests"""

    def test_version(self):
        """check pycistarget_core exposes a version attribute"""
        self.assertTrue(hasattr(pycistarget_core, "__version__"))
        self.assertIsInstance(pycistarget_core.__version__, str)


if __name__ == "__main__":
    unittest.main()
