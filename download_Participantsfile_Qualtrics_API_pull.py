import http.client 
import json
import time
import os
import csv

# Define paths
SURVEY_FILE = r"\Python Workspace\NexThink Project\survey_mapping.json"
LOG_DIR = r"Python Workspace\NexThink Project\Logs"
LOG_FILE = os.path.join(LOG_DIR, "download_log.csv")
OUTPUT_DIR = r"Python Workspace\NexThink Project\Participant List Output"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def load_survey_mapping():
    with open(SURVEY_FILE, "r") as f:
        return json.load(f)

survey_mapping = load_survey_mapping()

# Prompt user to select a survey
print("Available surveys:")
for survey in survey_mapping:
    print(survey)

selected_survey = input("\nEnter the survey name from the list above: ")

# Ensure the selected survey is valid
if selected_survey not in survey_mapping:
    print("Invalid survey name. Please restart the program and enter a valid survey.")
    exit()

project_id = survey_mapping[selected_survey]
print(f"Selected Survey: {selected_survey}, Project ID: {project_id}")

# Step 1: Retrieve jobID using POST request
conn = http.client.HTTPSConnection("iad1.qualtrics.com")

payload = "[\n\t\n]"  # Example payload if required
headers = {
    'Content-Type': "application/json",
    'X-API-TOKEN': "CkGZJX6qqbIbLhJ56yShuHoJKNdIojqVC3CNlfku"
}

conn.request("POST", f"/API/v3/ex-projects/{project_id}/export-participants/", payload, headers)
res = conn.getresponse()
data = res.read()
response_data = json.loads(data.decode("utf-8"))

job_id = response_data.get("jobId", None)

def log_status(survey_name, status):
    """Logs the status of the survey download."""
    with open(LOG_FILE, "a", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), survey_name, status])

if job_id:
    print(f"Retrieved Job ID: {job_id}")
    
    # Step 2: Make GET request using the retrieved jobID and retry until progressPercent == 100
    conn = http.client.HTTPSConnection("iad1.qualtrics.com")
    get_endpoint = f"/API/v3/ex-projects/{project_id}/export-participants/{job_id}"
    progress_percent = 0
    retry_count = 0

    while progress_percent < 100:
        conn.request("GET", get_endpoint, headers=headers)
        res = conn.getresponse()
        response_data = json.loads(res.read().decode("utf-8"))
        progress_percent = int(response_data.get("progressPercent", 0))
        print(f"Current progressPercent: {progress_percent}%")

        if progress_percent < 100:
            retry_count += 1
            print(f"Retrying... Attempt #{retry_count}")
            time.sleep(15)
        else:
            print("Task completed.")
            result_id = response_data.get("resultId", None)

            if result_id:
                print(f"Retrieved Result ID: {result_id}")
                result_endpoint = f"/API/v3/ex-projects/{project_id}/export-participants/results/{result_id}/file"
                conn.request("GET", result_endpoint, headers=headers)
                res = conn.getresponse()

                file_path = os.path.join(OUTPUT_DIR, f"ParticipantExport_{selected_survey}.csv")
                with open(file_path, "wb") as csv_file:
                    csv_file.write(res.read())

                print(f"CSV file downloaded successfully as {file_path}")
                log_status(selected_survey, "Success")
            else:
                print("Failed to retrieve resultId.")
                log_status(selected_survey, "Failure: No resultId")
else:
    print("Failed to retrieve Job ID.")
    log_status(selected_survey, "Failure: No jobId")
