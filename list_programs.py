"""Common list-operation examples.

Small runnable demos of Python list operations including negative number
filtering. All functions are pure and easy to unit test.
"""

from __future__ import annotations

from typing import List, Iterable


def filter_negative(numbers: Iterable[int]) -> List[int]:
    """Return only the negative integers from ``numbers`` in original order."""
    return [n for n in numbers if n < 0]


def filter_positive(numbers: Iterable[int]) -> List[int]:
    """Return only the positive integers from ``numbers`` in original order."""
    return [n for n in numbers if n > 0]


def filter_even(numbers: Iterable[int]) -> List[int]:
    """Return only the even integers from ``numbers``."""
    return [n for n in numbers if n % 2 == 0]


def filter_odd(numbers: Iterable[int]) -> List[int]:
    """Return only the odd integers from ``numbers``."""
    return [n for n in numbers if n % 2 == 1]


def squares(numbers: Iterable[int]) -> List[int]:
    """Return the square of each number in order."""
    return [n * n for n in numbers]


def cubes(numbers: Iterable[int]) -> List[int]:
    """Return the cube of each number in order."""
    return [n ** 3 for n in numbers]


def product(numbers: Iterable[int]) -> int:
    """Return the product of all numbers (empty input yields 1)."""
    result = 1
    for n in numbers:
        result *= n
    return result


def remove_duplicates(numbers: Iterable[int]) -> List[int]:
    """Return unique elements in first-occurrence order."""
    seen = set()
    out: List[int] = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def average(numbers: Iterable[int]) -> float:
    """Arithmetic mean of ``numbers``. Raises on empty input."""
    values = list(numbers)
    if not values:
        raise ValueError("Cannot compute average of empty sequence")
    return sum(values) / len(values)


def run_demo() -> None:
    """Print a quick demo of filter_negative."""
    data = [10, -5, 20, -15, 30, -25]
    print("Input     :", data)
    print("Negatives :", filter_negative(data))


if __name__ == "__main__":
    run_demo()
