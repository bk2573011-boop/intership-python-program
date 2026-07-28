# Library Management System
# Created by Bibha Kumari

library = []

def add_book():
    title = input("Enter book title: ")
    author = input("Enter author name: ")
    book = {"title": title, "author": author, "issued": False}
    library.append(book)
    print(f"'{title}' added to library successfully!\n")

def view_books():
    if not library:
        print("No books in library.\n")
        return
    print("\n----- Library Books -----")
    for i, book in enumerate(library, start=1):
        status = "Issued" if book["issued"] else "Available"
        print(f"{i}. {book['title']} by {book['author']} - {status}")
    print()

def issue_book():
    title = input("Enter book title to issue: ")
    for book in library:
        if book["title"].lower() == title.lower():
            if book["issued"]:
                print("Sorry, this book is already issued.\n")
            else:
                book["issued"] = True
                print(f"'{title}' issued successfully!\n")
            return
    print("Book not found.\n")

def return_book():
    title = input("Enter book title to return: ")
    for book in library:
        if book["title"].lower() == title.lower():
            if not book["issued"]:
                print("This book was not issued.\n")
            else:
                book["issued"] = False
                print(f"'{title}' returned successfully!\n")
            return
    print("Book not found.\n")

def search_book():
    title = input("Enter book title to search: ")
    for book in library:
        if book["title"].lower() == title.lower():
            status = "Issued" if book["issued"] else "Available"
            print(f"Found: {book['title']} by {book['author']} - {status}\n")
            return
    print("Book not found.\n")

def delete_book():
    title = input("Enter book title to delete: ")
    for book in library:
        if book["title"].lower() == title.lower():
            library.remove(book)
            print(f"'{title}' deleted from library.\n")
            return
    print("Book not found.\n")

def main():
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
            add_book()
        elif choice == "2":
            view_books()
        elif choice == "3":
            issue_book()
        elif choice == "4":
            return_book()
        elif choice == "5":
            search_book()
        elif choice == "6":
            delete_book()
        elif choice == "7":
            print("Thank you for using Library Management System!")
            break
        else:
            print("Invalid choice, try again.\n")

main()