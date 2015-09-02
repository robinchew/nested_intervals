from decimal import Decimal
import math


class Matrix(object):
    def __init__(self, a11, a12, a21, a22):
        self.a11 = a11
        self.a12 = a12
        self.a21 = a21
        self.a22 = a22

    def __repr__(self):
        return '{} {} {} {}'.format(self.a11, self.a12, self.a21, self.a22)

    def __mul__(self, m2):
        m1 = self
        return Matrix(
            m1.a11 * m2.a11 + m1.a12 * m2.a21,
            m1.a11 * m2.a12 + m1.a12 * m2.a22,
            m1.a21 * m2.a11 + m1.a22 * m2.a21,
            m1.a21 * m2.a12 + m1.a22 * m2.a22
        )

    def __iter__(self):
        for a in (self.a11, self.a12, self.a21, self.a22):
            yield a

ROOT_MATRIX = Matrix(1, -1, 1, 0)

def get_child_matrix(matrix, nth_child):
    """
    nth_child with value 1 repreesents the first child,
    and 2 represents the second child, etc.
    0 is an invalid nth_child value.
    """
    assert nth_child >= 1
    return matrix * Matrix(nth_child+1, -1, 1, 0)


def get_parent_matrix(matrix):
    nth_child = math.floor(abs(Decimal(matrix.a11)) / abs(Decimal(matrix.a12)))
    return Matrix(
        matrix.a11 * 0 + matrix.a12 * (-1),
        matrix.a11 * 1 + matrix.a12 * ((nth_child+1)),
        matrix.a21 * 0 + matrix.a22 * (-1),
        matrix.a21 * 1 + matrix.a22 * ((nth_child+1)))
