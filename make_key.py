"""
make_key.py — Naye customer ke liye API key banao (aasaan tool)
================================================================
Ye AAP (owner) chalate ho jab bhi naya customer aaye. Customer ko sirf jo
'API KEY' print hoti hai wahi deni hai — code/database kuch nahi.

CHALAO:
    python make_key.py "Customer Name" 10000
    python make_key.py "Sharma Motors" 10000 sharma@email.com

Args:
    1. customer_name  (zaroori)  — customer ka naam
    2. calls_per_month (optional, default 10000) — monthly limit
    3. email (optional)
"""

import sys
import api_keys


def main():
    if len(sys.argv) < 2:
        print("Usage: python make_key.py \"Customer Name\" [calls_per_month] [email]")
        print("Example: python make_key.py \"Sharma Motors\" 10000 sharma@email.com")
        return

    name = sys.argv[1]
    calls = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    email = sys.argv[3] if len(sys.argv) > 3 else None

    key = api_keys.create_customer_key(name, email, calls)

    print("=" * 60)
    print("  NAYI API KEY BAN GAYI!")
    print("=" * 60)
    print(f"  Customer : {name}")
    print(f"  Limit    : {calls:,} calls/month")
    if email:
        print(f"  Email    : {email}")
    print()
    print(f"  API KEY  : {key}")
    print("=" * 60)
    print("  Ye API KEY customer ko do (aur API_DOCS.md / customer guide).")
    print("  Code ya database kabhi mat dena — sirf ye key.")
    print("=" * 60)


if __name__ == "__main__":
    main()