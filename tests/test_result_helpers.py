import math
import unittest

import numpy as np

from febio_step.result_helpers import (
    calculate_compression_stiffness,
    calculate_cylinder_area,
    calculate_percent_difference,
    calculate_theoretical_compression_stiffness,
    maximum_magnitude,
)


class ResultHelperTests(unittest.TestCase):
    def test_cylinder_areas(self):
        self.assertAlmostEqual(
            calculate_cylinder_area("solid", 3.0, 2.0),
            9.0 * math.pi,
        )
        self.assertAlmostEqual(
            calculate_cylinder_area("hollow", 3.0, 2.0),
            5.0 * math.pi,
        )

    def test_theoretical_stiffness(self):
        expected = 193e9 * (5.0 * math.pi) / 15.0
        actual = calculate_theoretical_compression_stiffness(
            "hollow",
            outer_radius=3.0,
            inner_radius=2.0,
            height=15.0,
            young_modulus=193e9,
        )
        self.assertAlmostEqual(actual, expected)

    def test_compression_stiffness_uses_axial_force(self):
        reaction_forces = np.array(
            [
                [1.0, 2.0, 3.0],
                [-1.0, -2.0, 7.0],
            ]
        )
        total_force, axial_force, stiffness = calculate_compression_stiffness(
            reaction_forces,
            displacement=-0.5,
        )

        np.testing.assert_allclose(total_force, [0.0, 0.0, 10.0])
        self.assertEqual(axial_force, 10.0)
        self.assertEqual(stiffness, 20.0)

    def test_maximum_magnitude(self):
        values = np.array([[3.0, 4.0, 0.0], [1.0, 2.0, 2.0]])
        self.assertEqual(maximum_magnitude(values), 5.0)

    def test_percent_difference(self):
        self.assertEqual(calculate_percent_difference(101.0, 100.0), 1.0)

    def test_unknown_cylinder_type_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_cylinder_area("other", 3.0, 2.0)


if __name__ == "__main__":
    unittest.main()
