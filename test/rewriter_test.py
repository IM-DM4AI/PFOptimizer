import unittest
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


class RewriterCase(unittest.TestCase):
    def test_basic(self):
        print(DATA_PATH)
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
