import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("INVENTORY_DB_PATH", str(BASE_DIR / "inventory_ai.db"))

SECRET_KEY = os.environ.get("SECRET_KEY", "inventory-ai-secret-key-tamilnadu-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Indian Retail Defaults
DEFAULT_CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
DEFAULT_STATE = "Tamil Nadu"
DEFAULT_DISTRICT = "Chennai"

TAMIL_NADU_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
    "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
    "Vellore", "Viluppuram", "Virudhunagar"
]

GST_RATES = [0.0, 5.0, 12.0, 18.0, 28.0]
