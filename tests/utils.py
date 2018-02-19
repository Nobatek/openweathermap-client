"""Common tools for tests."""

try:
    from math import isclose  # flake8: noqa
except ImportError:
    def isclose(a, b, *args, rel_tol=1e-09, abs_tol=0.0):
        # pylint: disable=invalid-name, unused-argument
        """Return True if a and b values are close to each other, else False.

        Implemented in Python 3.5:
          https://docs.python.org/3/library/math.html#math.isclose
        """
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
