import os
from datetime import datetime, timezone
from tabulate import tabulate
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def add_member(name: str, email: str):
    resp = sb.table("members").insert({"name": name, "email": email}).execute()
    return resp.data

def get_member(member_id: int):
    resp = sb.table("members").select("*").eq("member_id", member_id).execute()
    return resp.data[0] if resp.data else None

def update_member(member_id: int, name=None, email=None):
    updates = {}
    if name: updates["name"] = name
    if email: updates["email"] = email
    if not updates: return None
    resp = sb.table("members").update(updates).eq("member_id", member_id).execute()
    return resp.data

def delete_member(member_id: int):
    active = sb.table("borrow_records").select("*").eq("member_id", member_id).is_("return_date", None).execute()
    if active.data:
        raise RuntimeError("Member has borrowed books not yet returned.")
    resp = sb.table("members").delete().eq("member_id", member_id).execute()
    return resp.data


def add_book(title, author, category, stock=1):
    resp = sb.table("books").insert({"title": title, "author": author, "category": category, "stock": stock}).execute()
    return resp.data

def update_book_stock(book_id: int, new_stock: int):
    resp = sb.table("books").update({"stock": new_stock}).eq("book_id", book_id).execute()
    return resp.data

def update_book_info(book_id: int, title=None, author=None, category=None):
    updates = {}
    if title: updates["title"] = title
    if author: updates["author"] = author
    if category: updates["category"] = category
    if not updates: return None
    resp = sb.table("books").update(updates).eq("book_id", book_id).execute()
    return resp.data

def delete_book(book_id: int):
    active = sb.table("borrow_records").select("*").eq("book_id", book_id).is_("return_date", None).execute()
    if active.data:
        raise RuntimeError("Book is currently borrowed; cannot delete.")
    resp = sb.table("books").delete().eq("book_id", book_id).execute()
    return resp.data

def list_books():
    resp = sb.table("books").select("*").order("title").execute()
    return resp.data

def search_books(term):
    resp = sb.table("books").select("*").or_(f"title.ilike.%{term}%,author.ilike.%{term}%,category.ilike.%{term}%").order("title").execute()
    return resp.data

def member_with_borrowed(member_id):
    resp = sb.table("borrow_records").select("*, books(title,author)").eq("member_id", member_id).order("borrow_date", desc=True).execute()
    return resp.data

def borrow_book(member_id: int, book_id: int):
    book = sb.table("books").select("*").eq("book_id", book_id).execute().data
    if not book:
        raise RuntimeError("Book not found.")
    stock = book[0]["stock"]
    if stock <= 0:
        raise RuntimeError("Book not available.")
    sb.table("books").update({"stock": stock - 1}).eq("book_id", book_id).execute()
    resp = sb.table("borrow_records").insert({"member_id": member_id, "book_id": book_id}).execute()
    return resp.data

def return_book(member_id: int, book_id: int):
    br = sb.table("borrow_records")\
        .select("*")\
        .eq("member_id", member_id)\
        .eq("book_id", book_id)\
        .is_("return_date", None)\
        .order("borrow_date", desc=True)\
        .limit(1)\
        .execute()
    
    if not br.data:
        raise RuntimeError("No active borrow record found.")
    
    record_id = br.data[0]["record_id"]
    

    now_utc = datetime.now(timezone.utc).isoformat()
    
    sb.table("borrow_records").update({"return_date": now_utc}).eq("record_id", record_id).execute()
    
    book = sb.table("books").select("stock").eq("book_id", book_id).execute().data[0]
    sb.table("books").update({"stock": book["stock"] + 1}).eq("book_id", book_id).execute()
    
    return {"record_id": record_id, "returned_at": now_utc}


def top_borrowed_books(limit=5):
    resp = sb.rpc("top_borrowed_books", {"p_limit": limit}).execute()
    return resp.data

def overdue_members(days=14):
    resp = sb.rpc("overdue_members", {"p_days": days}).execute()
    return resp.data

def borrowed_count_per_member():
    resp = sb.rpc("borrowed_count_per_member").execute()
    return resp.data

def print_table(rows, title="Results"):
    print(f"\n--- {title} ---")

    if not rows:
        print("No results.")
        return


    if len(rows) == 1 and isinstance(rows[0], dict) and len(rows[0]) == 1:
        rows = list(rows[0].values())[0]

    if not rows:
        print("No results.")
        return

    if isinstance(rows, dict):
        rows = [rows]

    if all(isinstance(r, dict) for r in rows):
        keys = rows[0].keys()
        table = [[r.get(k, "") for k in keys] for r in rows]
        print(tabulate(table, headers=keys, tablefmt="psql"))
        return

    if isinstance(rows[0], (list, tuple)):
        headers = [f"Col{i}" for i in range(len(rows[0]))]
        table = [list(r) for r in rows]
        print(tabulate(table, headers=headers, tablefmt="psql"))
        return

    print(rows)

def main_menu():
    while True:
        print("\n--- Library Management ---")
        print("1. Register member")
        print("2. Add book")
        print("3. List books")
        print("4. Search books")
        print("5. Member details & borrowed books")
        print("6. Update member")
        print("7. Update book stock/info")
        print("8. Delete member")
        print("9. Delete book")
        print("10. Borrow book")
        print("11. Return book")
        print("12. Reports")
        print("13. Exit")

        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                name = input("Name: ").strip()
                email = input("Email: ").strip()
                print(add_member(name, email))

            elif choice == "2":
                title = input("Title: ").strip()
                author = input("Author: ").strip()
                cat = input("Category: ").strip() or None
                stock = int(input("Stock: ").strip() or 1)
                print(add_book(title, author, cat, stock))

            elif choice == "3":
                rows = list_books()
                print_table(rows, "Books List")

            elif choice == "4":
                term = input("Search term: ").strip()
                rows = search_books(term)
                print_table(rows, "Search Results")

            elif choice == "5":
                mid = int(input("Member ID: ").strip())
                member = get_member(mid)
                print("Member:", member)
                borrowed = member_with_borrowed(mid)
                print_table(borrowed, "Borrowed Books")

            elif choice == "6":
                mid = int(input("Member ID: ").strip())
                new_name = input("New name (leave blank to skip): ").strip() or None
                new_email = input("New email (leave blank to skip): ").strip() or None
                print(update_member(mid, new_name, new_email))

            elif choice == "7":
                bid = int(input("Book ID: ").strip())
                new_stock = input("New stock (leave blank to skip): ").strip()
                if new_stock != "":
                    print(update_book_stock(bid, int(new_stock)))
                else:
                    new_title = input("New title (leave blank to skip): ").strip() or None
                    new_author = input("New author (leave blank to skip): ").strip() or None
                    new_cat = input("New category (leave blank to skip): ").strip() or None
                    print(update_book_info(bid, new_title, new_author, new_cat))

            elif choice == "8":
                mid = int(input("Member ID to delete: ").strip())
                print("Deleted:", delete_member(mid))

            elif choice == "9":
                bid = int(input("Book ID to delete: ").strip())
                print("Deleted:", delete_book(bid))

            elif choice == "10":
                mid = int(input("Member ID: ").strip())
                bid = int(input("Book ID: ").strip())
                print(borrow_book(mid, bid))

            elif choice == "11":
                mid = int(input("Member ID: ").strip())
                bid = int(input("Book ID: ").strip())
                print(return_book(mid, bid))

            elif choice == "12":
                print("\nReports:")
                print("a) Top borrowed books")
                print("b) Overdue (>14 days)")
                print("c) Borrowed count per member")
                r = input("Choose report: ").strip().lower()
                if r == "a":
                    rows = top_borrowed_books()
                    print_table(rows, "Top Borrowed Books")
                elif r == "b":
                    rows = overdue_members()
                    print_table(rows, "Overdue Members")
                elif r == "c":
                    rows = borrowed_count_per_member()
                    print_table(rows, "Borrowed Count per Member")
                else:
                    print("Invalid report option.")

            elif choice == "13":
                print("Bye.")
                break

            else:
                print("Invalid option.")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main_menu()
