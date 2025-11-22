# --- Config ---
QR_FILE = "kotaktotpqr.png"   # path to your QR image

# --- Imports ---
from PIL import Image
from pyzbar.pyzbar import decode
import urllib.parse, pyotp

# --- Decode QR ---
data = decode(Image.open(QR_FILE))
if not data:
    raise SystemExit("❌ No QR detected.")
uri = data[0].data.decode()
print("URI:", uri)

# --- Extract Secret ---
params = urllib.parse.parse_qs(urllib.parse.urlparse(uri).query)
secret = params.get("secret", [None])[0]
if not secret:
    raise SystemExit("❌ No secret found.")
print("Secret:", secret)

# --- Generate TOTP ---
print("Current TOTP:", pyotp.TOTP(secret).now())
