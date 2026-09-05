import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Lightweight .env loader (zero external dependency required)
def load_dotenv_file():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"[Config] Warning loading .env: {e}")

load_dotenv_file()

DB_PATH = os.environ.get("INVENTORY_DB_PATH", str(BASE_DIR / "inventory_ai.db"))

SECRET_KEY = os.environ.get("SECRET_KEY", "inventory-ai-secret-key-tamilnadu-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# LLM & AI Copilot Configuration (Free options: Gemini, Groq, Ollama, Built-in)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")  # 'auto', 'gemini', 'groq', 'ollama', 'built_in'

# Google Gemini (Free tier from https://aistudio.google.com/)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# Groq Cloud (Free tier from https://console.groq.com/)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# Ollama Local (100% Free Offline from https://ollama.com/)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

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

