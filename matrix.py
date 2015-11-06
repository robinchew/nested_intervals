from decimal import Decimal
from pyrsistent import pvector
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

    def __eq__(self, other):
        if self.a11 != other.a11:
            return False
        if self.a12 != other.a12:
            return False
        if self.a21 != other.a21:
            return False
        if self.a22 != other.a22:
            return False
        return True

    def __iter__(self):
        for a in (self.a11, self.a12, self.a21, self.a22):
            yield a

"""
This Nested Intervals is designed such that the database table does NOT
contain any row that represents the one true definitive original root matrix
that all nodes branches off from.

Any 'Root' row that exists in the database table is actually the child
of the invisible root.

Any model that calls get_ancestors will NEVER include an instance that
has the INVISIBLE_ROOT_MATRIX, because once again, the invisible root does
not exist in the database.
"""
INVISIBLE_ROOT_MATRIX = Matrix(1, -1, 1, 0)

def get_child_matrix(matrix, nth_child):
    """
    nth_child with value 1 repreesents the first child,
    and 2 represents the second child, etc.
    0 is an invalid nth_child value.
    """
    assert nth_child >= 1
    return matrix * Matrix(nth_child+1, -1, 1, 0)


def get_parent_matrix(matrix):
    nth_child = int(math.floor(abs(Decimal(matrix.a11)) / abs(Decimal(matrix.a12))))
    return Matrix(
        matrix.a11 * 0 + matrix.a12 * (-1),
        matrix.a11 * 1 + matrix.a12 * ((nth_child+1)),
        matrix.a21 * 0 + matrix.a22 * (-1),
        matrix.a21 * 1 + matrix.a22 * ((nth_child+1)))

def _build_ancestors_matrix(matrix, l):
    parent_matrix = get_parent_matrix(matrix)
    if parent_matrix == INVISIBLE_ROOT_MATRIX:
        return l
    return _build_ancestors_matrix(parent_matrix, l.append(parent_matrix))

def get_ancestors_matrix(matrix):
    return _build_ancestors_matrix(matrix, pvector())

def get_root_matrix(matrix):
    return get_ancestors_matrix(matrix)[-1]
