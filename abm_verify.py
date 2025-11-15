# pip install PyJWT cryptography requests
import os, time, uuid, requests, jwt
from cryptography.hazmat.primitives import serialization

CLIENT_ID = os.environ["ABM_CLIENT_ID"]    # e.g. BUSINESSAPI.6af2be19-...
KEY_ID    = os.environ["ABM_KEY_ID"]       # e.g. 93d2de38-...
KEY_PATH  = os.environ["ABM_KEY_PATH"]     # path to PKCS#8 EC P-256 private key

TOKEN_AUD = "https://account.apple.com/auth/oauth2/v2/token"
TOKEN_URL = "https://account.apple.com/auth/oauth2/token"
API_BASE  = "https://api-business.apple.com/v1"

# 1) Build client assertion (ES256, 15 min)
now = int(time.time())
payload = {
    "iss": CLIENT_ID,
    "sub": CLIENT_ID,
    "aud": TOKEN_AUD,
    "iat": now,
    "exp": now + 15*60,
    "jti": str(uuid.uuid4()),
}
headers = {"kid": KEY_ID, "alg": "ES256", "typ": "JWT"}
with open(KEY_PATH, "rb") as f:
    key = serialization.load_pem_private_key(f.read(), password=None)

assertion = jwt.encode(payload, key, algorithm="ES256", headers=headers)

# 2) Exchange for access token
resp = requests.post(
    TOKEN_URL,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "scope": "business.api",
    },
    timeout=30,
)
print("Token status:", resp.status_code)
print("Token body:", resp.text)
resp.raise_for_status()
access_token = resp.json()["access_token"]

# 3) Call the API
devices = requests.get(
    f"{API_BASE}/orgDevices",
    headers={"Authorization": f"Bearer {access_token}"},
    timeout=30,
)
print("Devices status:", devices.status_code)
print(devices.text)