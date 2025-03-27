import json
import base64
import requests
import time
from datetime import datetime
import secure_credentials  # Import the secure credentials helper module

# Constants
NQL_ID = "#qualtrics_user_query"
params = {}
output_file = "\\Python Workspace\\NexThink Project\\UserSID\\UserInfo_SID.csv"
instance_name = "K"
region = "us"
api_url = f"https://{instance_name}.api.{region}.nexthink.cloud/api"

# API Endpoints
api_endpoints = {
    "GET_TOKEN": f"{api_url}/v1/token",
    "NQL_EXPORT": f"{api_url}/v1/nql/export",
    "NQL_EXPORT_STATUS": f"{api_url}/v1/nql/status/"
}

# Load credentials securely
credentials = secure_credentials.decrypt_credentials()
client_id = credentials["client_id"]
client_secret = credentials["client_secret"]

# Encode authentication
auth_info = f"{client_id}:{client_secret}"
encoded_auth_info = base64.b64encode(auth_info.encode("utf-8")).decode("utf-8")

# Headers for token request
headers = {"Authorization": f"Basic {encoded_auth_info}"}

# Get API token
response = requests.post(api_endpoints["GET_TOKEN"], headers=headers)
if response.status_code != 200:
    print("Error fetching token:", response.text)
    exit()

token = response.json().get("access_token")
if not token:
    print("Token not found in response.")
    exit()

# Updated headers with Bearer token
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {token}"
}

# NQL Export Request
body = {
    "queryId": NQL_ID,
    "parameters": params
}

response = requests.post(api_endpoints["NQL_EXPORT"], headers=headers, json=body)
if response.status_code != 200:
    print("Error initiating export:", response.text)
    exit()

export_id = response.json().get("exportId")
if not export_id:
    print("Export ID not found in response.")
    exit()

# Wait for Export to Complete
export_status_url = f"{api_endpoints['NQL_EXPORT_STATUS']}{export_id}"
export_status = {}

while True:
    response = requests.get(export_status_url, headers=headers)
    if response.status_code != 200:
        print("Error checking export status:", response.text)
        exit()

    export_status = response.json()
    status = export_status.get("status")
    if status in ["ERROR", "COMPLETED"]:
        break

    print("Waiting for export to finish...")
    time.sleep(2)

# Download the File
if export_status.get("status") == "COMPLETED":
    print("Export completed. Downloading the CSV file...")
    results_file_url = export_status.get("resultsFileUrl")
    if not results_file_url:
        print("Results file URL not found in response.")
        exit()

    with requests.get(results_file_url, stream=True) as r:
        r.raise_for_status()
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"File downloaded to: {output_file}")
else:
    print("Error occurred during export:", export_status.get("errorDescription"))
