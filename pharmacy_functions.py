"""
PHARMACY DATA STORAGE
"""
ORDERS_DB = {
    "orders": {},
    "next_id": 1,
}


DRUG_DB = {
    "aspirin": {
        "name": "Acetylsalicylic Acid",
        "price": 50.00,
        "description": (
            "Non-steroidal anti-inflammatory drug for "
            "pain relief and fever reduction"
        ),
        "quantity": 30,
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "price": 80.00,
        "description": (
            "Anti-inflammatory medication for pain and "
            "inflammation management"
        ),
        "quantity": 20,
    },
    "acetaminophen": {
        "name": "Acetaminophen",
        "price": 60.00,
        "description": (
            "Analgesic and antipyretic medication for "
            "pain and fever control"
        ),
        "quantity": 25,
    },
    "metformin": {
        "name": "Metformin Hydrochloride",
        "price": 120.00,
        "description": (
            "Biguanide antidiabetic medication for "
            "type 2 diabetes management"
        ),
        "quantity": 60,
    },
    "lisinopril": {
        "name": "Lisinopril",
        "price": 90.00,
        "description": (
            "ACE inhibitor for hypertension and "
            "heart failure treatment"
        ),
        "quantity": 30,
    },
    "atorvastatin": {
        "name": "Atorvastatin Calcium",
        "price": 180.00,
        "description": (
            "HMG-CoA reductase inhibitor for "
            "cholesterol management"
        ),
        "quantity": 30,
    },
    "omeprazole": {
        "name": "Omeprazole",
        "price": 140.00,
        "description": (
            "Proton pump inhibitor for acid reflux "
            "and ulcer treatment"
        ),
        "quantity": 28,
    },
    "amlodipine": {
        "name": "Amlodipine Besylate",
        "price": 100.00,
        "description": (
            "Calcium channel blocker for hypertension "
            "and angina"
        ),
        "quantity": 30,
    },
    "metoprolol": {
        "name": "Metoprolol Tartrate",
        "price": 110.00,
        "description": (
            "Beta-blocker for hypertension and "
            "heart rhythm disorders"
        ),
        "quantity": 30,
    },
    "sertraline": {
        "name": "Sertraline Hydrochloride",
        "price": 250.00,
        "description": (
            "Selective serotonin reuptake inhibitor for "
            "depression and anxiety"
        ),
        "quantity": 30,
    },
}


"""
GET DRUG INFORMATION
"""
def get_drug_info(drug_name):
    drug = DRUG_DB.get(drug_name.lower())

    if drug:
        return {
            "name": drug["name"],
            "description": drug["description"],
            "price": drug["price"],
            "currency": "INR",
            "quantity": drug["quantity"],
        }
    return {"error": f"Drug '{drug_name}' not found"}


"""
PLACE PHARMACY ORDER
"""
def place_order(customer_name, drug_name):
    drug = DRUG_DB.get(drug_name.lower())

    if not drug:
        return {
            "error": f"Drug '{drug_name}' not found"
        }

    order_id = ORDERS_DB["next_id"]
    ORDERS_DB["next_id"] += 1
    order = {
        "id": order_id,
        "customer": customer_name,
        "drug": drug["name"],
        "quantity": drug["quantity"],
        "total": drug["price"],
        "currency": "INR",
        "status": "pending",
    }

    ORDERS_DB["orders"][order_id] = order
    return {
        "order_id": order_id,
        "message": (
            f"Order {order_id} placed: "
            f"{drug['quantity']} {drug['name']} "
            f"for ₹{order['total']:.2f}"
        ),
        "total": order["total"],
        "currency": order["currency"],
        "quantity": drug["quantity"],
    }


"""
LOOK UP PHARMACY ORDER
"""
def lookup_order(order_id):
    order_id = int(order_id)
    order = ORDERS_DB["orders"].get(order_id)

    if order:
        return {
            "order_id": order_id,
            "customer": order["customer"],
            "drug": order["drug"],
            "quantity": order["quantity"],
            "total": order["total"],
            "currency": order["currency"],
            "status": order["status"],
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