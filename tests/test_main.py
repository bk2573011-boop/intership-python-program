"""Tests for the Library Management System (main.py)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from main import (  # noqa: E402
    add_book,
    view_books,
    find_book,
    issue_book,
    return_book,
    search_book,
    delete_book,
)


def test_add_book_appends():
    lib = []
    ok = add_book(lib, "The Great Gatsby", "F. Scott Fitzgerald")
    assert ok is True
    assert len(lib) == 1
    assert lib[0]["title"] == "The Great Gatsby"
    assert lib[0]["author"] == "F. Scott Fitzgerald"
    assert lib[0]["issued"] is False


def test_view_books_empty():
    assert view_books([]) == []


def test_view_books_multiple():
    lib = []
    add_book(lib, "Book1", "A1")
    add_book(lib, "Book2", "A2")
    lines = view_books(lib)
    assert len(lines) == 2
    assert "Book1 by A1 - Available" in lines[0]
    assert "Book2 by A2 - Available" in lines[1]


def test_find_book_case_insensitive():
    lib = []
    add_book(lib, "Harry Potter", "JK Rowling")
    assert find_book(lib, "harry potter") is not None
    assert find_book(lib, "HARRY POTTER")["author"] == "JK Rowling"
    assert find_book(lib, "missing") is None


def test_issue_book_flow():
    lib = []
    add_book(lib, "Dune", "Frank Herbert")
    assert issue_book(lib, "dune") == "issued"
    assert issue_book(lib, "Dune") == "already_issued"
    assert issue_book(lib, "nope") == "not_found"
    book = find_book(lib, "Dune")
    assert book and book["issued"] is True


def test_return_book_flow():
    lib = []
    add_book(lib, "1984", "George Orwell")
    assert return_book(lib, "1984") == "not_issued"
    issue_book(lib, "1984")
    assert return_book(lib, "1984") == "returned"
    assert return_book(lib, "absent") == "not_found"
    book = find_book(lib, "1984")
    assert book and book["issued"] is False


def test_search_book_present_and_absent():
    lib = []
    add_book(lib, "Pride and Prejudice", "Jane Austen")
    result = search_book(lib, "pride and prejudice")
    assert result is not None
    assert "Jane Austen" in result
    assert "Available" in result
    issue_book(lib, "Pride and Prejudice")
    assert "Issued" in search_book(lib, "Pride and Prejudice")
    assert search_book(lib, "No Such Book") is None


def test_delete_book():
    lib = []
    add_book(lib, "Moby Dick", "Herman Melville")
    assert delete_book(lib, "moby dick") is True
    assert len(lib) == 0
    assert delete_book(lib, "Moby Dick") is False


def test_view_books_shows_issued_status():
    lib = []
    add_book(lib, "Issued", "IA")
    add_book(lib, "Avail", "AA")
    issue_book(lib, "Issued")
    lines = view_books(lib)
    assert any("Issued" in line and line.endswith("Issued") for line in lines)
    assert any("Avail" in line and line.endswith("Available") for line in lines)
