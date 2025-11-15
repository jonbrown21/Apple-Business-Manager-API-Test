# make_assertion.py
import os, time, uuid, jwt
from cryptography.hazmat.primitives import serialization

CLIENT_ID = os.environ["ABM_CLIENT_ID"]      # BUSINESSAPI.xxxxx...
KEY_ID    = os.environ["ABM_KEY_ID"]         # the GUID-like Key ID
KEY_PATH  = os.environ["ABM_KEY_PATH"]       # path to unencrypted PKCS#8 EC key (.pem)
TOKEN_URL = "https://account.apple.com/auth/oauth2/token"

with open(KEY_PATH, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

now = int(time.time())
claims = {
    "iss": CLIENT_ID,
    "sub": CLIENT_ID,
    "aud": TOKEN_URL,
    "iat": now,
    "exp": now + 300,
    "jti": str(uuid.uuid4())
}
headers = {"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}

print(jwt.encode(claims, private_key, algorithm="ES256", headers=headers))
