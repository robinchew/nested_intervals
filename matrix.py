class Matrix(object):
    def __init__(self, a11, a12, a21, a22):
        self.a11 = a11
        self.a12 = a12
        self.a21 = a21
        self.a22 = a22

    def __mul__(self, m2):
        m1 = self
        return Matrix(
            m1.a11 * m2.a11 + m1.a12 * m2.a21,
            m1.a11 * m2.a12 + m1.a12 * m2.a22,
            m1.a21 * m2.a11 + m1.a22 * m2.a21,
            m1.a21 * m2.a12 + m1.a22 * m2.a22
        )

    def __repr__(self):
        return '{} {} {} {}'.format(self.a11, self.a12, self.a21, self.a22)
