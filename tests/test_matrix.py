from django.test import TestCase

from nested_intervals.matrix import Matrix, get_ancestors_matrix


class MatrixTest(TestCase):
    def test_ancestors(self):
        self.assertEqual(
            get_ancestors_matrix(Matrix(7, -5, 10, -7)),
            [Matrix(5, -3, 7, -4), Matrix(3, -1, 4, -1)])
