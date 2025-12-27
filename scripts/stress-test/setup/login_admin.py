#!/usr/bin/env python3

import base64
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import httpx
from common import Logger, config_helper


def encrypt_password(password: str) -> str:
    """
    Encrypt password using Base64 encoding (same as frontend).
    
    This mimics the frontend's encryptPassword function in web/utils/encryption.ts:
    - Encodes password to UTF-8 bytes
    - Base64 encodes the bytes
    
    Args:
        password: Plain text password
        
    Returns:
        Base64 encoded password string
    """
    # Encode password to UTF-8 bytes, then Base64 encode
    utf8_bytes = password.encode("utf-8")
    base64_encoded = base64.b64encode(utf8_bytes).decode("utf-8")
    return base64_encoded


def login_admin() -> None:
    """Login with admin account and save access token."""

    log = Logger("Login")
    log.header("Admin Login")

    # Read admin credentials from config
    admin_config = config_helper.read_config("admin_config")

    if not admin_config:
        log.error("Admin config not found")
        log.info("Please run setup_admin.py first to create the admin account")
        return

    log.info(f"Logging in with email: {admin_config['email']}")

    # API login endpoint
    base_url = "http://localhost:5001"
    login_endpoint = f"{base_url}/console/api/login"

    # Prepare login payload
    # Encrypt password using Base64 (same as frontend)
    encrypted_password = encrypt_password(admin_config["password"])
    login_payload = {
        "email": admin_config["email"],
        "password": encrypted_password,
        "remember_me": True,
    }

    try:
        # Make the login request
        with httpx.Client() as client:
            response = client.post(
                login_endpoint,
                json=login_payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                log.success("Login successful!")

                # Extract token from response
                response_data = response.json()

                # Check if login was successful
                if response_data.get("result") != "success":
                    log.error(f"Login failed: {response_data}")
                    return

                # Tokens are stored in cookies, not in response body
                # Check all available cookies (may have __Host- prefix)
                all_cookies = dict(response.cookies)
                log.debug(f"All cookies from login: {list(all_cookies.keys())}")
                
                # Try different possible cookie names
                access_token = (
                    all_cookies.get("access_token") or
                    all_cookies.get("__Host-access_token") or
                    ""
                )
                refresh_token = (
                    all_cookies.get("refresh_token") or
                    all_cookies.get("__Host-refresh_token") or
                    ""
                )

                if not access_token:
                    log.error("No access token found in cookies")
                    log.debug(f"Response body: {json.dumps(response_data, indent=2)}")
                    log.debug(f"Available cookies: {list(all_cookies.keys())}")
                    return
                
                # Save all cookies for reuse in subsequent requests
                token_config = {
                    "email": admin_config["email"],
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "all_cookies": all_cookies,  # Save all cookies for reuse
                }

                # Save token config
                if config_helper.write_config("token_config", token_config):
                    log.info(f"Token saved to: {config_helper.get_config_path('benchmark_state')}")

                # Show truncated token for verification
                token_display = f"{access_token[:20]}..." if len(access_token) > 20 else "Token saved"
                log.key_value("Access token", token_display)

            elif response.status_code == 401:
                log.error("Login failed: Invalid credentials")
                log.debug(f"Response: {response.text}")
            else:
                log.error(f"Login failed with status code: {response.status_code}")
                log.debug(f"Response: {response.text}")

    except httpx.ConnectError:
        log.error("Could not connect to Dify API at http://localhost:5001")
        log.info("Make sure the API server is running with: ./dev/start-api")
    except Exception as e:
        log.error(f"An error occurred: {e}")


if __name__ == "__main__":
    login_admin()
