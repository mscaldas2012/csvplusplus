"""
Brazilian E-Commerce (Olist-style) → CSV++ Converter
=====================================================
Merges 5 source CSV files — which together represent a single business
concept (an order) — into ONE CSV++ file using two key CSV++ features:

  Feature 1 — Arrays of structured fields (items and payments)
  ─────────────────────────────────────────────────────────────
  Each order can have multiple line items and multiple payment methods.
  In the source data these live in separate files with one row per item/payment.
  CSV++ collapses them into a single row per order using array fields:

    items[](product_id^seller_id^category^price^freight)
    payments[](type^installments^value)

  Example values:
    items    → PROD-A01^SELL-X10^electronics^129.90^12.50~PROD-A02^SELL-X10^electronics^49.90^8.00
    payments → credit_card^3^200.30

  Feature 2 — Structured fields (review)
  ───────────────────────────────────────
  Each order has at most one review with multiple sub-fields (score, title,
  comment). Instead of a join to a separate file, it becomes one structured
  field in the same row:

    review^(score^title^comment)

  Example value:
    review → 5^Great purchase^Products arrived well packed and ahead of schedule

Source files consumed
─────────────────────
  source/orders.csv         — one row per order
  source/order_items.csv    — many rows per order  ← flattened to items[]
  source/order_payments.csv — many rows per order  ← flattened to payments[]
  source/order_reviews.csv  — one row per order    ← embedded as review^()
  source/customers.csv      — one row per customer ← joined inline

Output
──────
  ecommerce_orders.csvpp    — one row per order, all data in one file

Usage:
    python convert_to_csvpp.py
"""

import csv
import os
from collections import defaultdict

HERE    = os.path.dirname(os.path.abspath(__file__))
SRC     = os.path.join(HERE, "source")
OUTPUT  = os.path.join(HERE, "ecommerce_orders.csvpp")

ARRAY_SEP     = "~"   # between array elements    (CSV++ default)
COMPONENT_SEP = "^"   # between struct components (CSV++ default)


# ── helpers ──────────────────────────────────────────────────────────────────

def read_csv(filename):
    path = os.path.join(SRC, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe(value):
    """Strip whitespace and replace any stray component/array separators."""
    return str(value).strip().replace(COMPONENT_SEP, ",").replace(ARRAY_SEP, ",")


def make_item(row):
    """One order_items row → one structured element: product_id^seller_id^category^price^freight"""
    return COMPONENT_SEP.join([
        safe(row["product_id"]),
        safe(row["seller_id"]),
        safe(row["product_category"]),
        safe(row["price"]),
        safe(row["freight_value"]),
    ])


def make_payment(row):
    """One order_payments row → one structured element: type^installments^value"""
    return COMPONENT_SEP.join([
        safe(row["payment_type"]),
        safe(row["payment_installments"]),
        safe(row["payment_value"]),
    ])


def make_review(row):
    """One order_reviews row → one structured field value: score^title^comment"""
    if row is None:
        return ""
    return COMPONENT_SEP.join([
        safe(row["review_score"]),
        safe(row["review_comment_title"]),
        safe(row["review_comment_message"]),
    ])


# ── load source tables ────────────────────────────────────────────────────────

orders    = read_csv("orders.csv")
customers = {r["customer_id"]: r for r in read_csv("customers.csv")}
reviews   = {r["order_id"]: r   for r in read_csv("order_reviews.csv")}

# Group items and payments by order_id (preserving insertion order)
items_by_order    = defaultdict(list)
payments_by_order = defaultdict(list)

for row in read_csv("order_items.csv"):
    items_by_order[row["order_id"]].append(row)

for row in sorted(read_csv("order_payments.csv"),
                  key=lambda r: int(r["payment_sequential"])):
    payments_by_order[row["order_id"]].append(row)


# ── write CSV++ output ────────────────────────────────────────────────────────

# CSV++ header:
#   items[](product_id^seller_id^category^price^freight)  ← typed array of structs
#   payments[](type^installments^value)                    ← typed array of structs
#   review^(score^title^comment)                          ← single structured field
FIELDNAMES = [
    "order_id",
    "customer_id",
    "customer_city",
    "customer_state",
    "order_status",
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "items[](product_id^seller_id^category^price^freight)",
    "payments[](type^installments^value)",
    "review^(score^title^comment)",
]

stats = {
    "orders": 0,
    "items_collapsed": 0,
    "payment_rows_collapsed": 0,
    "reviews_embedded": 0,
    "orders_no_review": 0,
}

with open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
    writer = csv.DictWriter(fout, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    for order in orders:
        oid  = order["order_id"]
        cust = customers.get(order["customer_id"], {})
        rev  = reviews.get(oid)

        order_items    = items_by_order.get(oid, [])
        order_payments = payments_by_order.get(oid, [])

        items_value    = ARRAY_SEP.join(make_item(i)    for i in order_items)
        payments_value = ARRAY_SEP.join(make_payment(p) for p in order_payments)
        review_value   = make_review(rev)

        writer.writerow({
            "order_id":                       oid,
            "customer_id":                    order["customer_id"],
            "customer_city":                  cust.get("customer_city", ""),
            "customer_state":                 cust.get("customer_state", ""),
            "order_status":                   order["order_status"],
            "order_purchase_timestamp":       order["order_purchase_timestamp"],
            "order_delivered_customer_date":  order["order_delivered_customer_date"],
            "order_estimated_delivery_date":  order["order_estimated_delivery_date"],
            "items[](product_id^seller_id^category^price^freight)": items_value,
            "payments[](type^installments^value)":                   payments_value,
            "review^(score^title^comment)":                          review_value,
        })

        stats["orders"] += 1
        stats["items_collapsed"]          += len(order_items)
        stats["payment_rows_collapsed"]   += len(order_payments)
        stats["reviews_embedded"]         += 1 if rev else 0
        stats["orders_no_review"]         += 0 if rev else 1


# ── report ────────────────────────────────────────────────────────────────────

print(f"\n✓ Conversion complete → {OUTPUT}\n")
print(f"  Source files consumed        : 5")
print(f"  Orders written               : {stats['orders']}")
print(f"  Item rows collapsed          : {stats['items_collapsed']}  (into items[] arrays)")
print(f"  Payment rows collapsed       : {stats['payment_rows_collapsed']}  (into payments[] arrays)")
print(f"  Reviews embedded             : {stats['reviews_embedded']}  (as review^() struct fields)")
print(f"  Orders with no review        : {stats['orders_no_review']}")
print()
print("  CSV++ features used:")
print("    items[](product_id^seller_id^category^price^freight)  — array of structs")
print("    payments[](type^installments^value)                    — array of structs")
print("    review^(score^title^comment)                          — single struct field")
print()
print("  What a standard CSV parser sees:   valid CSV, one row per order")
print("  What a CSV++ parser additionally:  typed arrays + structs, no JOINs needed")
