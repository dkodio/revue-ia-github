import unittest
from example_app.calculator import divide


class CalculatorTests(unittest.TestCase):
    def test_nominal(self):
        self.assertEqual(divide(8, 2), 4)

    def test_zero(self):
        with self.assertRaisesRegex(ValueError, "division par zero"):
            divide(8, 0)

    def test_negative(self):
        self.assertEqual(divide(-8, 2), -4)
