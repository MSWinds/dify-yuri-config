#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import time

import httpx
from common import Logger, config_helper


def install_openai_plugin() -> None:
    """Install OpenAI plugin using saved access token."""

    log = Logger("InstallPlugin")
    log.header("Installing OpenAI Plugin")

    # Read token and CSRF token from config
    access_token = config_helper.get_token()
    csrf_token = config_helper.get_csrf_token()
    if not access_token:
        log.error("No access token found in config")
        log.info("Please run login_admin.py first to get access token")
        return
    if not csrf_token:
        log.warning("No CSRF token found in config - requests may fail")

    log.step("Installing OpenAI plugin...")

    # API endpoint for plugin installation
    base_url = "http://localhost:5001"
    install_endpoint = f"{base_url}/console/api/workspaces/current/plugin/install/marketplace"

    # Plugin identifier
    plugin_payload = {
        "plugin_unique_identifiers": [
            "langgenius/openai:0.2.5@373362a028986aae53a7baf73a7f11991ba3c22c69eaf97d6cde048cfd4a9f98"
        ]
    }

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
        "Authorization": f"Bearer {access_token}",  # Use capital A for Authorization header
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
        # Make the installation request
        # Use cookies parameter directly - httpx will handle cookie formatting
        with httpx.Client() as client:
            response = client.post(
                install_endpoint,
                json=plugin_payload,
                headers=headers,
                cookies=all_cookies,  # Use cookies parameter directly
            )

            if response.status_code == 200:
                response_data = response.json()
                task_id = response_data.get("task_id")

                if not task_id:
                    log.error("No task ID received from installation request")
                    log.debug(f"Response data: {json.dumps(response_data, indent=2)}")
                    # Check if plugin is already installed
                    if "already" in str(response_data).lower() or "installed" in str(response_data).lower():
                        log.warning("Plugin may already be installed, skipping...")
                        return
                    return

                log.progress(f"Installation task created: {task_id}")
                log.info("Polling for task completion...")

                # Poll for task completion
                task_endpoint = f"{base_url}/console/api/workspaces/current/plugin/tasks/{task_id}"

                max_attempts = 30  # 30 attempts with 2 second delay = 60 seconds max
                attempt = 0

                log.spinner_start("Installing plugin")

                while attempt < max_attempts:
                    attempt += 1
                    time.sleep(2)  # Wait 2 seconds between polls

                    task_response = client.get(
                        task_endpoint,
                        headers=headers,
                        cookies=cookies,
                    )

                    if task_response.status_code != 200:
                        log.spinner_stop(
                            success=False,
                            message=f"Failed to get task status: {task_response.status_code}",
                        )
                        return

                    task_data = task_response.json()
                    task_info = task_data.get("task", {})
                    status = task_info.get("status")

                    if status == "success":
                        log.spinner_stop(success=True, message="Plugin installed!")
                        log.success("OpenAI plugin installed successfully!")

                        # Display plugin info
                        plugins = task_info.get("plugins", [])
                        if plugins:
                            plugin_info = plugins[0]
                            log.key_value("Plugin ID", plugin_info.get("plugin_id"))
                            log.key_value("Message", plugin_info.get("message"))
                        break

                    elif status == "failed":
                        log.spinner_stop(success=False, message="Installation failed")
                        log.error("Plugin installation failed")
                        plugins = task_info.get("plugins", [])
                        if plugins:
                            for plugin in plugins:
                                log.list_item(f"{plugin.get('plugin_id')}: {plugin.get('message')}")
                        break

                    # Continue polling if status is "pending" or other

                else:
                    log.spinner_stop(success=False, message="Installation timed out")
                    log.error("Installation timed out after 60 seconds")

            elif response.status_code == 401:
                log.error("Installation failed: Unauthorized")
                log.info("Token may have expired. Please run login_admin.py again")
            elif response.status_code == 409:
                log.warning("Plugin may already be installed")
                log.debug(f"Response: {response.text}")
            else:
                log.error(f"Installation failed with status code: {response.status_code}")
                log.debug(f"Response: {response.text}")

    except httpx.ConnectError:
        log.error("Could not connect to Dify API at http://localhost:5001")
        log.info("Make sure the API server is running with: ./dev/start-api")
    except Exception as e:
        log.error(f"An error occurred: {e}")


if __name__ == "__main__":
    install_openai_plugin()
