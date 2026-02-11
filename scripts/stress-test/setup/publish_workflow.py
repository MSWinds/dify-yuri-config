#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json

import httpx
from common import Logger, config_helper


def publish_workflow() -> None:
    """Publish the imported workflow app."""

    log = Logger("PublishWorkflow")
    log.header("Publishing Workflow")

    # Read token and CSRF token from config
    access_token = config_helper.get_token()
    csrf_token = config_helper.get_csrf_token()
    if not access_token:
        log.error("No access token found in config")
        return
    if not csrf_token:
        log.warning("No CSRF token found in config - requests may fail")

    # Read app_id from config
    app_id = config_helper.get_app_id()
    if not app_id:
        log.error("No app_id found in config")
        return

    log.step(f"Publishing workflow for app: {app_id}")

    # API endpoint for publishing workflow
    base_url = "http://localhost:5001"
    publish_endpoint = f"{base_url}/console/api/apps/{app_id}/workflows/publish"

    # Publish payload
    publish_payload = {"marked_name": "", "marked_comment": ""}

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "http://localhost:3000",
        "Pragma": "no-cache",
        "Referer": "http://localhost:3000/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf_token if csrf_token else "",  # CSRF token required for console API
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    # Get all cookies from login (includes access_token with correct name, possibly __Host- prefix)
    all_cookies = config_helper.get_all_cookies()
    all_cookies["locale"] = "en-US"

    try:
        # Make the publish request
        # Use cookies parameter directly - httpx will handle cookie formatting
        with httpx.Client() as client:
            response = client.post(
                publish_endpoint,
                json=publish_payload,
                headers=headers,
                cookies=all_cookies,  # Use cookies parameter directly
            )

            if response.status_code == 200 or response.status_code == 201:
                log.success("Workflow published successfully!")
                log.key_value("App ID", app_id)

                # Try to parse response if it has JSON content
                if response.text:
                    try:
                        response_data = response.json()
                        if response_data:
                            log.debug(f"Response: {json.dumps(response_data, indent=2)}")
                    except json.JSONDecodeError:
                        # Response might be empty or non-JSON
                        pass

            elif response.status_code == 401:
                log.error("Workflow publish failed: Unauthorized")
                log.info("Token may have expired. Please run login_admin.py again")
            elif response.status_code == 404:
                log.error("Workflow publish failed: App not found")
                log.info("Make sure the app was imported successfully")
            else:
                log.error(f"Workflow publish failed with status code: {response.status_code}")
                log.debug(f"Response: {response.text}")

    except httpx.ConnectError:
        log.error("Could not connect to Dify API at http://localhost:5001")
        log.info("Make sure the API server is running with: ./dev/start-api")
    except Exception as e:
        log.error(f"An error occurred: {e}")


if __name__ == "__main__":
    publish_workflow()
