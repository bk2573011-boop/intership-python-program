"""Library Management System.

Created by Bibha Kumari

A command-line application for managing a library's book inventory with
add/view/issue/return/search/delete operations.
"""

from __future__ import annotations

from typing import List, Dict, Optional


def add_book(library: List[Dict], title: str, author: str) -> bool:
    """Add a new book to the library.

    Args:
        library: The library list to mutate.
        title: Book title.
        author: Book author.

    Returns:
        True when the book was appended.
    """
    book: Dict = {"title": title, "author": author, "issued": False}
    library.append(book)
    return True


def view_books(library: List[Dict]) -> List[str]:
    """Return a human-readable list of books with their status.

    Args:
        library: The library list.

    Returns:
        A list of formatted strings, one per book. Empty list when no books.
    """
    lines: List[str] = []
    for i, book in enumerate(library, start=1):
        status = "Issued" if book["issued"] else "Available"
        lines.append(f"{i}. {book['title']} by {book['author']} - {status}")
    return lines


def find_book(library: List[Dict], title: str) -> Optional[Dict]:
    """Find a book by title (case-insensitive).

    Args:
        library: The library list.
        title: Title to search for.

    Returns:
        The first matching book dict, or ``None``.
    """
    needle = title.lower()
    for book in library:
        if book["title"].lower() == needle:
            return book
    return None


def issue_book(library: List[Dict], title: str) -> str:
    """Issue a book.

    Returns:
        A short status message: "issued", "already_issued", or "not_found".
    """
    book = find_book(library, title)
    if book is None:
        return "not_found"
    if book["issued"]:
        return "already_issued"
    book["issued"] = True
    return "issued"


def return_book(library: List[Dict], title: str) -> str:
    """Return (un-issue) a book.

    Returns:
        "returned", "not_issued", or "not_found".
    """
    book = find_book(library, title)
    if book is None:
        return "not_found"
    if not book["issued"]:
        return "not_issued"
    book["issued"] = False
    return "returned"


def search_book(library: List[Dict], title: str) -> Optional[str]:
    """Search for a book and return its status line, or None when absent."""
    book = find_book(library, title)
    if book is None:
        return None
    status = "Issued" if book["issued"] else "Available"
    return f"{book['title']} by {book['author']} - {status}"


def delete_book(library: List[Dict], title: str) -> bool:
    """Delete the first book matching title. Returns True on success."""
    book = find_book(library, title)
    if book is None:
        return False
    library.remove(book)
    return True


def _prompt_add_book(library: List[Dict]) -> None:
    title = input("Enter book title: ")
    author = input("Enter author name: ")
    add_book(library, title, author)
    print(f"'{title}' added to library successfully!\n")


def _prompt_view_books(library: List[Dict]) -> None:
    lines = view_books(library)
    if not lines:
        print("No books in library.\n")
        return
    print("\n----- Library Books -----")
    for line in lines:
        print(line)
    print()


def _prompt_issue_book(library: List[Dict]) -> None:
    title = input("Enter book title to issue: ")
    result = issue_book(library, title)
    if result == "issued":
        print(f"'{title}' issued successfully!\n")
    elif result == "already_issued":
        print("Sorry, this book is already issued.\n")
    else:
        print("Book not found.\n")


def _prompt_return_book(library: List[Dict]) -> None:
    title = input("Enter book title to return: ")
    result = return_book(library, title)
    if result == "returned":
        print(f"'{title}' returned successfully!\n")
    elif result == "not_issued":
        print("This book was not issued.\n")
    else:
        print("Book not found.\n")


def _prompt_search_book(library: List[Dict]) -> None:
    title = input("Enter book title to search: ")
    result = search_book(library, title)
    if result is None:
        print("Book not found.\n")
    else:
        print(f"Found: {result}\n")


def _prompt_delete_book(library: List[Dict]) -> None:
    title = input("Enter book title to delete: ")
    if delete_book(library, title):
        print(f"'{title}' deleted from library.\n")
    else:
        print("Book not found.\n")


def run_cli() -> None:
    """Run the interactive command-line interface for the library system."""
    library: List[Dict] = []
    print("===== Library Management System =====")
    while True:
        print("1. Add Book")
        print("2. View Books")
        print("3. Issue Book")
        print("4. Return Book")
        print("5. Search Book")
        print("6. Delete Book")
        print("7. Exit")
        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            _prompt_add_book(library)
        elif choice == "2":
            _prompt_view_books(library)
        elif choice == "3":
            _prompt_issue_book(library)
        elif choice == "4":
            _prompt_return_book(library)
        elif choice == "5":
            _prompt_search_book(library)
        elif choice == "6":
            _prompt_delete_book(library)
        elif choice == "7":
            print("Thank you for using Library Management System!")
            break
        else:
            print("Invalid choice, try again.\n")


if __name__ == "__main__":
    run_cli()
