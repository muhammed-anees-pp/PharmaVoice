from pharmacy_storage import create_order
from pharmacy_storage import get_drug
from pharmacy_storage import get_order
from pharmacy_storage import get_order_history


"""
GET DRUG INFORMATION
"""
def get_drug_info(drug_name):
    drug = get_drug(drug_name)

    if drug:
        return {
            "name": drug["name"],
            "description": drug["description"],
            "price": drug["price"],
            "currency": drug["currency"],
            "quantity": drug["package_quantity"],
            "available_stock": drug["stock"],
        }

    return {"error": f"Drug '{drug_name}' not found"}


"""
PLACE PHARMACY ORDER
"""
def place_order(customer_name, drug_name):
    order = create_order(customer_name, drug_name)

    if not order:
        return {
            "error": f"Drug '{drug_name}' not found"
        }

    return {
        "order_id": order["order_id"],
        "message": (
            f"Order {order['order_id']} placed: "
            f"{order['quantity']} {order['drug']} "
            f"for ₹{order['total']:.2f}"
        ),
        "total": order["total"],
        "currency": order["currency"],
        "quantity": order["quantity"],
        "status": order["status"],
    }


"""
LOOK UP PHARMACY ORDER
"""
def lookup_order(order_id):
    try:
        order = get_order(order_id)
        history = get_order_history(order_id)
    except (TypeError, ValueError):
        return {"error": f"Invalid order ID: {order_id}"}

    if order:
        return {
            "order_id": order["order_id"],
            "customer": order["customer"],
            "drug": order["drug"],
            "quantity": order["quantity"],
            "total": order["total"],
            "currency": order["currency"],
            "status": order["status"],
            "status_history": [
                {
                    "status": item["status"],
                    "note": item["note"],
                    "created_at": item["created_at"],
                }
                for item in history
            ],
        }

    return {"error": f"Order {order_id} not found"}


"""
FUNCTION REGISTRY
"""
FUNCTION_MAP = {
    "get_drug_info": get_drug_info,
    "place_order": place_order,
    "lookup_order": lookup_order,
}

