# Apple Business Manager API Playground

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Playground-yellow)

![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![PyJWT](https://img.shields.io/badge/PyJWT-ES256-blue)
![Cryptography](https://img.shields.io/badge/Cryptography-PEM%20Keys-purple)

![ABM API](https://img.shields.io/badge/Apple%20Business%20Manager-API-black?logo=apple)
![OAuth2](https://img.shields.io/badge/OAuth2-Client%20Credentials-orange)
![JWT](https://img.shields.io/badge/JWT-ES256-important)

![macOS 15 Tahoe](https://img.shields.io/badge/macOS-15%20Tahoe-00aaff)
![Learning Project](https://img.shields.io/badge/Project-Learning-lightgrey)
![Human Written](https://img.shields.io/badge/AI-Free%20Commit%20Messages-ff69b4)
![Custom](https://img.shields.io/badge/ABM%20Key-ES256%20PKCS8-blue)

---

This repository is a **playground for learning and testing the Apple Business Manager (ABM) API**. It focuses on the end-to-end process of:

- Creating a **client assertion (JWT)** signed with your ABM API private key  
- Exchanging that assertion for an **OAuth 2.0 access token**  
- Calling the **Apple Business Manager Device Management API** (e.g. `/v1/orgDevices`)  

Along the way, it documents the **gotchas** around Apple’s certificate/key workflow, including how to **decrypt and convert the private key with OpenSSL** so Python can use it.

---

## Repository layout

- `make_assertion.py`  
  Builds and prints a short-lived **ES256 JWT client assertion** using your ABM API credentials and unencrypted PKCS#8 EC private key.

- `abm_verify.py`  
  Uses your ABM credentials and unencrypted PKCS#8 EC private key to:  
  1. Build an ES256 client assertion  
  2. Exchange it for an access token  
  3. Call the `/v1/orgDevices` endpoint and print the result  
  This script is a simple “does it all work?” verification tool.

---

## What you need before running anything

### 1. An Apple Business Manager API client

In Apple Business Manager you must:

1. Sign in with an account that can manage API access.  
2. Create an **API client** (sometimes labeled as “Device Management API” or similar).  
3. When you create the client, Apple will give you:  
   - **Client ID** (e.g. `BUSINESSAPI.6af2be19-…`)  
   - **Key ID** (a GUID-like value)  
   - A **downloadable key file / certificate** (this is where the OpenSSL conversion comes in)

> **Important:** Apple’s key material is typically **encrypted or wrapped**. Python’s `cryptography` library requires an **unencrypted PKCS#8 EC P-256 key in PEM format**. The steps below describe how to get there.

---

## Converting the ABM key with OpenSSL

The scripts expect `ABM_KEY_PATH` to point to an **unencrypted PKCS#8 EC P-256 private key** in PEM format.

Depending on what Apple gives you, you may have either:

- A **`.p12` / `.pfx` file** (PKCS#12, password-protected)  
- A **password-protected PEM**  
- Or a **plain `.p8` private key** that’s already usable

Below are common OpenSSL flows. You may only need **one or two** of these examples.

### A. Starting from a `.p12` (PKCS#12) file

1. **Export the private key from the PKCS#12 bundle** (will likely prompt for the export password):

```bash
openssl pkcs12 -in abm_client.p12 -nocerts -nodes -out abm_key.pem
```

2. **Convert to unencrypted PKCS#8 PEM** (the format the scripts expect):

```bash
openssl pkcs8 -topk8 -inform PEM -outform PEM   -in abm_key.pem   -out abm_key_unencrypted.pem   -nocrypt
```

Now set `ABM_KEY_PATH` to the full path of `abm_key_unencrypted.pem`.

### B. Starting from a password-protected PEM key

If you already have a PEM key that’s encrypted with a passphrase:

```bash
openssl pkcs8 -topk8 -inform PEM -outform PEM   -in encrypted_key.pem   -out abm_key_unencrypted.pem   -nocrypt
```

OpenSSL will prompt you for the passphrase, and produce an **unencrypted** PKCS#8 PEM.

### C. Starting from an Apple `.p8` key

If Apple gives you a `.p8` key that looks like this:

```text
-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
```

…it may **already** be an unencrypted PKCS#8 EC key. In that case you can usually rename it and use it directly:

```bash
cp AuthKey_XXXXXXX.p8 abm_key_unencrypted.pem
```

If Python later complains that it can’t deserialize the key, convert it with the `pkcs8 -topk8` command as shown above.

---

## Python environment & dependencies

These scripts require:

- **Python 3.9+** (3.11+ recommended)
- The following Python packages:

```bash
pip install PyJWT cryptography requests
```

You can install them globally or inside a virtualenv/venv—your choice.

---

## Environment variables

Both scripts use the same three environment variables:

- `ABM_CLIENT_ID`  
  The **Client ID** Apple shows when you create the API client  
  (e.g. `BUSINESSAPI.6af2be19-...`)

- `ABM_KEY_ID`  
  The **Key ID** associated with your ABM API key (a GUID-like string)

- `ABM_KEY_PATH`  
  The **absolute or relative path** to your unencrypted PKCS#8 EC P-256 private key file  
  (e.g. `/Users/you/keys/abm_key_unencrypted.pem`)

### Setting these on macOS (zsh)

```bash
export ABM_CLIENT_ID="BUSINESSAPI.6af2be19-..."
export ABM_KEY_ID="93d2de38-..."
export ABM_KEY_PATH="/Users/you/keys/abm_key_unencrypted.pem"
```

You can put those in your shell profile (`~/.zshrc`) or just export them in the terminal before running the scripts.

---

## Script 1: `make_assertion.py`

This script **builds and prints a client assertion JWT**. It’s a good first step to confirm:

- Your key is readable  
- Your environment variables are correct  
- The JWT looks sane and decodes as expected

### What it does

- Loads the private key from `ABM_KEY_PATH` using the `cryptography` library  
- Builds a JWT with:
  - `iss`: your `ABM_CLIENT_ID`  
  - `sub`: your `ABM_CLIENT_ID`  
  - `aud`: Apple’s token URL (`https://account.apple.com/auth/oauth2/token`)  
  - `iat`: current UNIX timestamp  
  - `exp`: `iat + 300` seconds (5 minutes)  
  - `jti`: a random UUID
- Signs it with ES256 using your private key and `ABM_KEY_ID` as the `kid` header

### How to run

```bash
python make_assertion.py
```

If everything is configured correctly, it prints a **compact JWT string** to stdout (one long line of `eyJhbGciOi...`).

You can paste that JWT into a tool like [jwt.io](https://jwt.io/) to inspect the header and claims and confirm:

- `alg` is `ES256`  
- `kid` matches your `ABM_KEY_ID`  
- `iss` and `sub` are your `ABM_CLIENT_ID`  
- `aud` is `https://account.apple.com/auth/oauth2/token`  

---

## Script 2: `abm_verify.py`

This is the “full flow” script: it **builds the assertion, exchanges it for an access token, and hits the ABM API**.

### What it does, step by step

1. **Builds a client assertion** (ES256, 15-minute lifetime) using:
   - `iss` = `ABM_CLIENT_ID`
   - `sub` = `ABM_CLIENT_ID`
   - `aud` = `https://account.apple.com/auth/oauth2/v2/token`
   - `iat` = now
   - `exp` = now + 15 minutes
   - `jti` = random UUID

2. **Exchanges the assertion for an access token**  
   Sends a POST to Apple’s token endpoint:

   - URL: `https://account.apple.com/auth/oauth2/token`
   - Content-Type: `application/x-www-form-urlencoded`
   - Params:
     - `grant_type=client_credentials`
     - `client_id=<your ABM_CLIENT_ID>`
     - `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer`
     - `client_assertion=<JWT from step 1>`
     - `scope=business.api`

   On success, Apple returns a JSON object containing an `access_token`.

3. **Calls the ABM API**  
   Uses the access token to call:

   - `GET https://api-business.apple.com/v1/orgDevices`
   - Header: `Authorization: Bearer <access_token>`

4. **Prints the status codes and bodies** to your terminal so you can see exactly what Apple returns during both token and API calls.

### How to run

```bash
python abm_verify.py
```

You should see output similar to:

```text
Token status: 200
Token body: {"access_token":"...","token_type":"Bearer","expires_in":900,...}
Devices status: 200
{"data":[ ... orgDevices payload ... ]}
```

If you get `401`, `403`, or another error, see the troubleshooting section below.

---

## Common gotchas & troubleshooting

### 1. “Could not deserialize key data” / key loading errors

If Python throws an error like:

> Could not deserialize key data. The data may be in an incorrect format, the provided password may be incorrect, or it may be an unsupported key type.

Check:

- `ABM_KEY_PATH` is correct  
- The file is **unencrypted** (no passphrase required)  
- The file is **PKCS#8** (`-----BEGIN PRIVATE KEY-----`) rather than legacy PKCS#1 or other formats  

If needed, re-run the OpenSSL conversion to ensure `-nocrypt` and `-topk8` were used.

### 2. 400/401 errors from the token endpoint

Typical causes:

- `ABM_CLIENT_ID` doesn’t match the client associated with your key  
- `ABM_KEY_ID` is wrong or doesn’t match the key file  
- The **JWT `aud` claim** doesn’t match the token URL Apple expects  
- System clock skew: if your machine’s time is far off, `iat`/`exp` may be invalid

Things to verify:

- Re-copy `ABM_CLIENT_ID` and `ABM_KEY_ID` from ABM  
- Make sure the **client assertion lifetime** is short (5–15 minutes) and uses the proper `aud`  
- Make sure your host time is reasonably accurate (e.g., via system time sync)

### 3. 403 / permission issues when calling `/v1/orgDevices`

If the token request succeeds but the devices request fails:

- Confirm the API client in ABM is granted the **correct scopes/permissions**  
- Ensure that you’re using **`scope=business.api`** in the token request  
- Double-check that your ABM account actually has devices and that your organization is configured for the Device Management API

### 4. OpenSSL “Can’t open input/output file” errors

When running the OpenSSL commands:

- Ensure the **paths are correct and quoted** if they contain spaces
- If you see `Can't open input file`, check that the source file exists  
- If you see `Can't open output file`, make sure the directory is writable

Example with spaces in the path:

```bash
openssl pkcs12 -in "/Users/you/ABM Keys/abm_client.p12" -nocerts -nodes -out "/Users/you/ABM Keys/abm_key.pem"
```

---

## Understanding the overall flow

Conceptually, this playground is modeling the standard **OAuth 2.0 client_credentials + JWT client authentication** flow that Apple uses:

1. **ABM issues you a credential set**:
   - `Client ID`
   - `Key ID`
   - Encrypted key/cert material

2. **You convert the key into a runtime-usable format**:
   - Unencrypted PKCS#8 EC P-256 PEM

3. **Your client (these scripts) builds a signed JWT**:
   - Claims: who you are (`iss/sub`), who it’s for (`aud`), validity period (`iat/exp`), unique ID (`jti`)
   - Header: algorithm (`ES256`), key id (`kid`)

4. **You exchange that JWT for an access token**:
   - POST to Apple’s token endpoint
   - Get back a short-lived bearer token

5. **You call the ABM API with that token**:
   - `Authorization: Bearer <access_token>`
   - Hit endpoints like `/v1/orgDevices`

This repo keeps each step **small and inspectable**, so you can learn what’s happening at each stage rather than hiding everything in a single monolithic script.

