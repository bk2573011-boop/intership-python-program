"""Student Marks Calculator.

Takes student name and 5 subject marks, prints total, percentage, grade,
and pass/fail status.
"""

from __future__ import annotations

from typing import Dict, Tuple, Any


NUM_SUBJECTS = 5


def calculate_result(marks: Tuple[float, ...]) -> Dict[str, Any]:
    """Compute total, percentage and grade from a 5-tuple of marks.

    Args:
        marks: A tuple of marks with exactly NUM_SUBJECTS elements.

    Returns:
        A dict with keys ``total`` (float), ``percentage`` (float),
        and ``grade`` (str).
    """
    if len(marks) != NUM_SUBJECTS:
        raise ValueError(f"Expected {NUM_SUBJECTS} marks, got {len(marks)}")
    total = sum(marks)
    percentage = total / NUM_SUBJECTS

    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "F"

    return {"total": total, "percentage": percentage, "grade": grade}


def is_pass(grade: str) -> bool:
    """Return True if the grade is a passing grade."""
    return grade != "F"


def run_cli() -> None:
    """Run the interactive marks calculator."""
    print("===== Student Marks Calculator =====")

    name = input("Enter Student Name: ")
    marks = []
    for i in range(1, NUM_SUBJECTS + 1):
        marks.append(float(input(f"Enter marks for Subject {i}: ")))

    result = calculate_result(tuple(marks))
    passed = is_pass(result["grade"])

    print("\n===== Result =====")
    print("Student Name :", name)
    print("Total Marks  :", result["total"], f"/{NUM_SUBJECTS * 100}")
    print("Percentage   :", result["percentage"], "%")
    print("Grade        :", result["grade"])
    print("Result       :", "Pass" if passed else "Fail")


if __name__ == "__main__":
    run_cli()
