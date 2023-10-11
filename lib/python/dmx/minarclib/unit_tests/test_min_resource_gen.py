import unittest

from dmx.minarclib.parse_audit_files import generate_min_resources

class TestMinResourceGen(unittest.TestCase):

    def test_outputs(self):
        print str(generate_min_resources())

if __name__ == '__main__':
    unittest.main()
