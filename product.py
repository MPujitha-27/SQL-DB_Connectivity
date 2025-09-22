import os
from supabase import create_client, Client 
from dotenv import load_dotenv 
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)
def add_product(name, sku, price, stock):
    payload = {"name": name, "sku": sku, "price": price, "stock": stock}
    resp = sb.table("products1").insert(payload).execute()
    return resp.data
def update_product(sku, name=None, price=None, stock=None):
    payload = {}
    if name is not None:
        payload["name"] = name
    if price is not None:
        payload["price"] = price
    if stock is not None:
        payload["stock"] = stock
    if not payload:
        print("Nothing to update!")
        return None
    resp = sb.table("products1").update(payload).eq("sku", sku).execute()
    return resp.data

def delete_product(sku):
    resp = sb.table("products1").delete().eq("sku", sku).execute()
    return resp.data

def list_products():
    resp = sb.table("products1").select("*").execute()
    return resp.data

if __name__ == "__main__":
    while True:
        print("\n--- Product Management ---")
        print("1. Add Product")
        print("2. Update Product")
        print("3. Delete Product")
        print("4. List Products")
        print("5. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            name = input("Enter product name: ").strip()
            sku = input("Enter SKU: ").strip()
            price = float(input("Enter price: ").strip())
            stock = int(input("Enter stock: ").strip())
            created = add_product(name, sku, price, stock)
            print("Inserted:", created)

        elif choice == "2":
            sku = input("Enter SKU of product to update: ").strip()
            name = input("Enter new name (leave blank to skip): ").strip() or None
            price_input = input("Enter new price (leave blank to skip): ").strip()
            price = float(price_input) if price_input else None
            stock_input = input("Enter new stock (leave blank to skip): ").strip()
            stock = int(stock_input) if stock_input else None
            updated = update_product(sku, name, price, stock)
            print("Updated:", updated)

        elif choice == "3":
            sku = input("Enter SKU of product to delete: ").strip()
            deleted = delete_product(sku)
            print("Deleted:", deleted)

        elif choice == "4":
            products = list_products()
            for p in products:
                print(p)

        elif choice == "5":
            print("Exiting program.")
            break

        else:
            print("Invalid choice. Try again.")
 
 
