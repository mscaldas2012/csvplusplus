# CSV++ Example: E-Commerce Orders

> **Inspired by:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle, 100k orders)
> **Sample size:** 10 orders — representative of the full dataset structure
> **Source format:** 5 separate CSV files (standard RFC 4180)
> **Target format:** 1 CSV++ file ([draft-mscaldas-csvpp-02](https://csvplusplus.com))

---

## The Problem: 5 Files to Describe One Thing

An e-commerce order is a single business concept. But flat CSV can't represent
one-to-many relationships, so it gets shattered across multiple files:

```
source/
├── orders.csv          ← 1 row per order       (status, timestamps)
├── order_items.csv     ← 1 row per LINE ITEM   (many per order)
├── order_payments.csv  ← 1 row per PAYMENT     (many per order — split payments!)
├── order_reviews.csv   ← 1 row per review      (joined separately)
└── customers.csv       ← 1 row per customer    (joined by customer_id)
```

A single order with 3 items paid via credit card + voucher produces:
- **1 row** in `orders.csv`
- **3 rows** in `order_items.csv`
- **2 rows** in `order_payments.csv`
- **1 row** in `order_reviews.csv`
- **1 row** in `customers.csv`

That's **8 rows across 5 files** to represent one order. Every consumer of
this data has to reassemble it with JOINs and `groupby`:

```python
# What every data team writes today
orders = pd.read_csv("orders.csv")
items  = pd.read_csv("order_items.csv")
pays   = pd.read_csv("order_payments.csv")
revs   = pd.read_csv("order_reviews.csv")
custs  = pd.read_csv("customers.csv")

items_agg = items.groupby("order_id").apply(lambda g: g.to_dict("records"))
pays_agg  = pays.groupby("order_id").apply(lambda g: g.to_dict("records"))

df = (orders
      .merge(custs,     on="customer_id")
      .merge(items_agg, on="order_id")
      .merge(pays_agg,  on="order_id")
      .merge(revs,      on="order_id", how="left"))
```

**CSV++ eliminates all of this.** One file. One row per order. All data present.

---

## The Solution: Two CSV++ Features

### Feature 1 — Arrays of structured fields

Line items and payments are **one-to-many**: each order can have multiple of
them. CSV++ expresses this with a typed array declaration in the column header:

```
items[](product_id^seller_id^category^price^freight)
```

Breaking this down:
- `items` — the field name
- `[]` — this field is an **array** (multiple values)
- `(product_id^seller_id^category^price^freight)` — each element is a **struct** with these named components, separated by `^`

**Multiple items in one cell** (separated by `~`):
```
PROD-A01^SELL-X10^electronics^129.90^12.50~PROD-A02^SELL-X10^electronics^49.90^8.00
```

The same pattern applies to payments — capturing split-payment reality:
```
payments[](type^installments^value)
credit_card^6^150.30~voucher^1^51.50
```

### Feature 2 — Single structured fields

A review has **one-to-one** cardinality (at most one per order) but contains
multiple sub-fields. Instead of a separate file, it becomes a struct:

```
review^(score^title^comment)
5^Great purchase^Products arrived well packed and ahead of schedule. Very happy!
```

Empty when no review exists (orders ORD-0009, ORD-0010):
```
review^(score^title^comment)

```

---

## Before and After: Order ORD-0003

This order has 3 items, a split payment (credit card + voucher), and a 3-star review.

### Before — 8 rows across 5 files

**orders.csv:**
```
ORD-0003,CUST-103,delivered,2023-03-14 15:33:10,...
```

**order_items.csv** (3 rows):
```
ORD-0003,1,PROD-C01,SELL-Z30,health_beauty,39.90,6.50
ORD-0003,2,PROD-C02,SELL-Z30,health_beauty,59.90,6.50
ORD-0003,3,PROD-C03,SELL-W40,sports_leisure,89.90,14.00
```

**order_payments.csv** (2 rows):
```
ORD-0003,1,credit_card,6,150.30
ORD-0003,2,voucher,1,51.50
```

**order_reviews.csv:**
```
REV-003,ORD-0003,3,Average experience,Products were fine but delivery took longer...
```

**customers.csv:**
```
CUST-103,30112,Belo Horizonte,MG
```

### After — 1 row in 1 file

```
ORD-0003,CUST-103,Belo Horizonte,MG,delivered,2023-03-14 15:33:10,2023-03-24 09:00:00,2023-03-30 00:00:00,PROD-C01^SELL-Z30^health_beauty^39.90^6.50~PROD-C02^SELL-Z30^health_beauty^59.90^6.50~PROD-C03^SELL-W40^sports_leisure^89.90^14.00,credit_card^6^150.30~voucher^1^51.50,3^Average experience^Products were fine but delivery took longer than expected.
```

Everything about this order — its items, how it was paid, what the customer
thought — is in a single, self-describing row.

---

## Conversion Stats (this sample)

| Metric                       | Value |
|------------------------------|-------|
| Source files consumed        | 5     |
| Orders in output             | 10    |
| Item rows collapsed          | 17   → `items[]` arrays |
| Payment rows collapsed       | 12   → `payments[]` arrays |
| Reviews embedded             | 8    → `review^()` struct fields |
| Orders with no review        | 2    (empty struct field) |

---

## Backward Compatibility

A standard CSV parser opening `ecommerce_orders.csvpp` sees perfectly valid CSV.
The column headers are legal strings. The `~` and `^` characters inside field
values are just characters — they don't break quoting or parsing.

```python
import pandas as pd
df = pd.read_csv("ecommerce_orders.csvpp")
# Works fine. items column is a string like "PROD-A01^SELL-X10^...~PROD-A02^..."
```

A CSV++ parser additionally understands the declarations and returns structured data:

```python
import csvpp
df = csvpp.read("ecommerce_orders.csvpp")
df["items"][0]     # → list of dicts, one per line item
df["payments"][0]  # → list of dicts, one per payment method
df["review"][0]    # → dict with score, title, comment keys
```

---

## Files in This Folder

```
ecommerce/
├── source/
│   ├── orders.csv           ← source: one row per order
│   ├── order_items.csv      ← source: one row per item (many per order)
│   ├── order_payments.csv   ← source: one row per payment (many per order)
│   ├── order_reviews.csv    ← source: one row per review
│   └── customers.csv        ← source: one row per customer
├── ecommerce_orders.csvpp   ← OUTPUT: one row per order, all data merged
├── convert_to_csvpp.py      ← the converter (zero dependencies, stdlib only)
└── README.md                ← this file
```

## Run It

```bash
python convert_to_csvpp.py
```

Requires Python 3.6+, no external dependencies.

---

## Scaling Up

This sample uses 10 orders. The real [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
has 100,000+ orders spread across the same schema. The converter works
identically — swap the source files and re-run.

---

## Learn More

- **Spec:** [csvplusplus.com](https://csvplusplus.com)
- **IETF Draft:** [draft-mscaldas-csvpp-02](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
- **Original dataset:** [Brazilian E-Commerce Public Dataset by Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
