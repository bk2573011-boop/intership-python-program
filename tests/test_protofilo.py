"""Tests for the Student Marks Calculator (protofilo.py)."""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from protofilo import calculate_result, is_pass, NUM_SUBJECTS  # noqa: E402


def test_grade_aplus():
    res = calculate_result((100.0, 100.0, 100.0, 100.0, 100.0))
    assert res["total"] == 500.0
    assert res["percentage"] == 100.0
    assert res["grade"] == "A+"
    assert is_pass(res["grade"]) is True


def test_grade_a():
    res = calculate_result((85.0, 85.0, 85.0, 85.0, 85.0))
    assert res["percentage"] == 85.0
    assert res["grade"] == "A"
    assert is_pass(res["grade"]) is True


def test_grade_b():
    res = calculate_result((75.0, 75.0, 75.0, 75.0, 75.0))
    assert res["grade"] == "B"


def test_grade_c_boundary():
    res = calculate_result((60.0, 60.0, 60.0, 60.0, 60.0))
    assert res["percentage"] == 60.0
    assert res["grade"] == "C"


def test_grade_d_and_pass():
    res = calculate_result((50.0, 50.0, 50.0, 50.0, 50.0))
    assert res["grade"] == "D"
    assert is_pass(res["grade"]) is True


def test_grade_f_and_fail():
    res = calculate_result((40.0, 40.0, 40.0, 40.0, 40.0))
    assert res["percentage"] == 40.0
    assert res["grade"] == "F"
    assert is_pass(res["grade"]) is False


def test_grade_f_zero():
    res = calculate_result((0.0, 0.0, 0.0, 0.0, 0.0))
    assert res["total"] == 0.0
    assert res["grade"] == "F"


def test_wrong_marks_count_raises():
    with pytest.raises(ValueError):
        calculate_result((1.0, 2.0, 3.0, 4.0))
    with pytest.raises(ValueError):
        calculate_result((1.0, 2.0, 3.0, 4.0, 5.0, 6.0))


def test_num_subjects_constant():
    assert NUM_SUBJECTS == 5
