"""
database_mock.py
-----------------
Fake e-commerce database for "TechMarket" (electronics store).
This simulates what would normally be a real DB (Postgres, MongoDB, etc.)
The Action Agent calls these functions instead of hitting a real API.
"""

from datetime import datetime
from typing import Optional


# ============================================================
# FAKE DATA
# ============================================================

CUSTOMERS = {
    "CUST001": {
        "customer_id": "CUST001",
        "name": "Sarah Ben Ali",
        "email": "sarah.benali@email.com",
        "loyalty_tier": "gold",
        "since": "2022-03-15",
    },
    "CUST002": {
        "customer_id": "CUST002",
        "name": "Karim Trabelsi",
        "email": "karim.trabelsi@email.com",
        "loyalty_tier": "silver",
        "since": "2023-07-01",
    },
    "CUST003": {
        "customer_id": "CUST003",
        "name": "Lina Mansour",
        "email": "lina.mansour@email.com",
        "loyalty_tier": "bronze",
        "since": "2024-01-10",
    },
}

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


# ============================================================
# HELPER FUNCTIONS (ce que l'Action Agent va appeler)
# ============================================================

def get_order_status(order_id: str) -> Optional[dict]:
    """Returns order info or None if not found."""
    return ORDERS.get(order_id)


def get_orders_by_customer(customer_id: str) -> list:
    """Returns all orders for a given customer."""
    return [o for o in ORDERS.values() if o["customer_id"] == customer_id]


def get_customer(customer_id: str) -> Optional[dict]:
    return CUSTOMERS.get(customer_id)


def get_product(product_id: str) -> Optional[dict]:
    return PRODUCTS.get(product_id)


def check_refund_eligibility(order_id: str) -> dict:
    """
    Business rule: refund eligible within 30 days of delivery,
    and only if status == 'delivered'.
    """
    order = ORDERS.get(order_id)
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



def update_stock(product_id: str, quantity_delta: int) -> Optional[dict]:
    """Simulates updating stock (e.g. after a cancelled order)."""
    product = PRODUCTS.get(product_id)
    if not product:
        return None
    product["stock"] = max(0, product["stock"] + quantity_delta)
    return product


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    print("Order ORD5001:", get_order_status("ORD5001"))
    print("Refund check ORD5002:", check_refund_eligibility("ORD5002"))