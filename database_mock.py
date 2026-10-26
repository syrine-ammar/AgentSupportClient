"""
database_mock.py
-----------------
Persistent fake e-commerce database using JSON files.
The Action Agent calls these functions instead of hitting a real API.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
ORDERS_FILE = DATA_DIR / "orders.json"
USERS_FILE = DATA_DIR / "users.json"

DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# FAKE DATA
# ============================================================
"""
CUSTOMERS = {
    "CUST001": {
        "customer_id": "CUST001",
        "name": "Sarah Ben Ali",
        "email": "sarah.benali@email.com",
        "phone": "+216 98 123 456",
        "loyalty_tier": "gold",
        "since": "2022-03-15",
    },
    "CUST002": {
        "customer_id": "CUST002",
        "name": "Karim Trabelsi",
        "email": "karim.trabelsi@email.com",
        "phone": "+216 99 234 567",
        "loyalty_tier": "silver",
        "since": "2023-07-01",
    },
    "CUST003": {
        "customer_id": "CUST003",
        "name": "Lina Mansour",
        "email": "lina.mansour@email.com",
        "phone": "+216 97 345 678",
        "loyalty_tier": "bronze",
        "since": "2024-01-10",
    },
}



ORDERS = {
    "ORD5001": {
        "order_id": "ORD5001",
        "customer_id": "CUST001",
        "products": ["PROD100"],
        "status": "shipped",
        "order_date": "2026-06-10",
        "delivery_date": "2026-06-18",
        "total": 1299.0,
        "tracking_number": "TM-994821-FR",
    },
    "ORD5002": {
        "order_id": "ORD5002",
        "customer_id": "CUST002",
        "products": ["PROD101"],
        "status": "delivered",
        "order_date": "2026-05-28",
        "delivery_date": "2026-06-02",
        "total": 89.0,
        "tracking_number": "TM-994822-FR",
    },
    "ORD5003": {
        "order_id": "ORD5003",
        "customer_id": "CUST003",
        "products": ["PROD102", "PROD101"],
        "status": "processing",
        "order_date": "2026-06-22",
        "delivery_date": None,
        "total": 148.0,
        "tracking_number": None,
    },
}

"""
PRODUCTS = {
    "PROD100": {
        "product_id": "PROD100",
        "name": "UltraBook Pro 14",
        "category": "laptop",
        "price": 1299.0,
        "stock": 14,
        "warranty_months": 24,
        "specs": "Intel i7, 16GB RAM, 512GB SSD, Windows 11 compatible",
    },
    "PROD101": {
        "product_id": "PROD101",
        "name": "SoundMax Wireless Headphones",
        "category": "audio",
        "price": 89.0,
        "stock": 0,
        "warranty_months": 12,
        "specs": "Bluetooth 5.3, 30h battery, active noise cancellation",
    },
    "PROD102": {
        "product_id": "PROD102",
        "name": "SmartHome Router X3",
        "category": "networking",
        "price": 59.0,
        "stock": 42,
        "warranty_months": 12,
        "specs": "WiFi 6, dual-band, supports up to 50 devices",
    },
}
# ============================================================
# HELPER FUNCTIONS (ce que l'Action Agent va appeler)
# ============================================================

# ============================================================
# LOAD / SAVE HELPERS
# ============================================================
def load_orders() -> dict:
    if not ORDERS_FILE.exists():
        return {}
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_orders(orders: dict):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

def load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# CUSTOMER FUNCTIONS
# ============================================================
def get_customer(customer_id: str) -> Optional[dict]:
    """Get customer info from users.json"""
    users = load_users()
    for user in users.values():
        if user.get("customer_id") == customer_id and user.get("status") == "approved":
            return {
                "customer_id": user["customer_id"],
                "name": user["name"],
                "email": user["email"],
                "phone": user.get("phone", "Not provided"),
                "loyalty_tier": user.get("loyalty_tier", "bronze"),
                "since": user.get("created_at", "")[:10]
            }
    return None

# ============================================================
# ORDER FUNCTIONS
# ============================================================
def get_order_status(order_id: str) -> Optional[dict]:
    orders = load_orders()
    return orders.get(order_id)

def get_orders_by_customer(customer_id: str) -> list:
    orders = load_orders()
    return [o for o in orders.values() if o["customer_id"] == customer_id]

def check_refund_eligibility(order_id: str) -> dict:
    order = get_order_status(order_id)
    if not order:
        return {"eligible": False, "reason": "order_not_found"}

    if order["status"] != "delivered":
        return {"eligible": False, "reason": "order_not_delivered_yet"}

    delivery_date = datetime.strptime(order["delivery_date"], "%Y-%m-%d")
    days_since_delivery = (datetime.now() - delivery_date).days

    if days_since_delivery > 30:
        return {
            "eligible": False,
            "reason": "outside_30_day_window",
            "days_since_delivery": days_since_delivery,
        }

    return {
        "eligible": True,
        "days_since_delivery": days_since_delivery,
        "order_total": order["total"],
    }

def get_product(product_id: str) -> Optional[dict]:
    return PRODUCTS.get(product_id)

def create_fake_orders_for_customer(customer_id: str) -> list:
    """Create 2-3 fake orders and save them in orders.json"""
    orders = load_orders()

    existing_ids = [
        int(oid.replace("ORD", ""))
        for oid in orders.keys()
        if oid.startswith("ORD") and oid.replace("ORD", "").isdigit()
    ]
    next_id = max(existing_ids, default=5000) + 1

    fake_orders = [
        {
            "order_id": f"ORD{next_id}",
            "customer_id": customer_id,
            "products": ["PROD100"],
            "status": "processing",
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "delivery_date": None,
            "total": 1299.0,
            "tracking_number": None,
        },
        {
            "order_id": f"ORD{next_id + 1}",
            "customer_id": customer_id,
            "products": ["PROD102", "PROD101"],
            "status": "shipped",
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "delivery_date": datetime.now().strftime("%Y-%m-%d"),
            "total": 148.0,
            "tracking_number": f"TM-{next_id + 1:06d}-FR",
        },
        {
            "order_id": f"ORD{next_id + 2}",
            "customer_id": customer_id,
            "products": ["PROD101"],
            "status": "delivered",
            "order_date": "2026-07-15",
            "delivery_date": "2026-07-20",
            "total": 89.0,
            "tracking_number": f"TM-{next_id + 2:06d}-FR",
        },
    ]

    for order in fake_orders:
        orders[order["order_id"]] = order

    save_orders(orders)
    return fake_orders