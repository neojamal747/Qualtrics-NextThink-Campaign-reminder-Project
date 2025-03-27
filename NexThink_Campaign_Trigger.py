import pandas as pd
import base64
import requests
import json
import os
from datetime import datetime, timedelta
import time
import secure_credentials  # Import the secure credentials helper module
import urllib.parse

# Configurable settings
REMINDER_MINUTES = 1  # Minutes before sending a reminder
MAX_REMINDERS = 3  # Maximum reminders allowed
LOG_LEVEL = "DEBUG"  # Options: "INFO", "DEBUG"
parameter1_Description = 'Hello, I am testing this reminder module for People Analytics and want you to take the sample survey.'
parameter2_Description ='[Click here](https://kenvuewfa.qualtrics.com/jfe/form/SV_d0eSKXOOZdZndTE?Q_TS_ID=TS_A1Pac9XSOyVsmQ3&Q_TS_RS=Self&Q_EE_ANON=1&_=1) to take the survey.'

# File paths
user_info_path = r"Python Workspace\NexThink Project\UserSID\TestUserInfo_SID.csv"
waiting_participants_path = r"Python Workspace\NexThink Project\Filtered Participants\Waiting_ParticipantsTEST.csv"
log_file_path = r"Python Workspace\NexThink Project\Logs\Campaign_Log.csv"

# Load data
user_info_df = pd.read_csv(user_info_path, usecols=['user.sid', 'user.ad.email_address'])
waiting_participants_df = pd.read_csv(waiting_participants_path, usecols=['Email'])

# Merge on email column
merged_df = pd.merge(
    waiting_participants_df,
    user_info_df,
    left_on='Email',
    right_on='user.ad.email_address',
    how='inner'
)

# Extract user.sids into a list
user_sids = merged_df['user.sid'].tolist()

# Load existing log data
if os.path.exists(log_file_path):
    log_df = pd.read_csv(log_file_path)
else:
    log_df = pd.DataFrame(columns=["Timestamp", "User_SID", "Status", "Reminder_Count"])

# Convert timestamp column to datetime
log_df["Timestamp"] = pd.to_datetime(log_df["Timestamp"], errors='coerce')

# API Configuration
instance_name = "kenvue"
region = "us"
input_campaign_id = "#testing_survey"

# Securely load encrypted credentials
credentials = secure_credentials.decrypt_credentials()
client_id = credentials["client_id"]
client_secret = credentials["client_secret"]

# API URLs
api_url = f"https://{instance_name}.api.{region}.nexthink.cloud/api"
api_endpoints = {
    "get_token": f"{api_url}/v1/token",
    "campaign_trigger": f"{api_url}/v1/euf/campaign/trigger",
}

# Encode credentials for authentication
auth_info = f"{client_id}:{client_secret}"
encoded_auth_info = base64.b64encode(auth_info.encode('utf-8')).decode('utf-8')
basic_auth_value = f"Basic {encoded_auth_info}"

# Step 1: Get API Token
headers = {"Authorization": basic_auth_value}
response = requests.post(api_endpoints["get_token"], headers=headers)
response.raise_for_status()

# Extract access token
token = response.json().get('access_token')
headers["Authorization"] = f"Bearer {token}"

# Step 2: Initialize Logging
log_data = []
skipped_users = []

# Step 3: Trigger Campaign for Eligible Users
for user_sid in user_sids:
    user_log = log_df[log_df["User_SID"] == user_sid]
    
    if not user_log.empty:
        last_reminder_date = user_log["Timestamp"].max()
        reminder_count = user_log["Reminder_Count"].max()
        minutes_since_last = (datetime.now() - last_reminder_date).total_seconds() / 60
        
        if reminder_count >= MAX_REMINDERS:
            skipped_users.append({"User_SID": user_sid, "Reason": "Max reminders reached"})
            continue
        if minutes_since_last < REMINDER_MINUTES:
            skipped_users.append({"User_SID": user_sid, "Reason": "1 minute threshold not met"})
            continue
        reminder_count += 1  # Increment reminder count
    else:
        reminder_count = 1  # First reminder
    
    # Send API request
    body_args = {
        "campaignNqlId": input_campaign_id,
        "userSid": [user_sid],
        "expiresInMinutes": 5,
        "parameters": {
            "user": 'Employee',
            "param_id_1": parameter1_Description,
            "param_id_2": parameter2_Description
            }
        }
    
    response = requests.post(api_endpoints["campaign_trigger"], headers=headers, json=body_args)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_json = response.json()
    
    if "requests" in response_json:
        campaign_status = "Success"
    else:
        campaign_status = f"Failed: {response_json}"
    
    log_data.append({
        "Timestamp": current_time,
        "User_SID": user_sid,
        "Status": campaign_status,
        "Reminder_Count": reminder_count
    })
    
    time.sleep(1)  # Adjust to avoid rate limiting

# Step 4: Save Log File
log_df = pd.concat([log_df, pd.DataFrame(log_data)], ignore_index=True)
log_df.to_csv(log_file_path, mode='w', header=True, index=False)

# Step 5: Log Skipped Users
if skipped_users and LOG_LEVEL == "DEBUG":
    skipped_log_file = log_file_path.replace("Campaign_Log.csv", "Skipped_Users_Log.csv")
    skipped_df = pd.DataFrame(skipped_users)
    skipped_df.to_csv(skipped_log_file, mode='w', header=True, index=False)
    print(f"Skipped users log updated: {skipped_log_file}")

print(f"Campaign log updated: {log_file_path}")
