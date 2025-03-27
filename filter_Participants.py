import pandas as pd

# Load the participant CSV file
file_path = r"Python Workspace\NexThink Project\Participant List Output\ParticipantExport_Exit Survey 2023.csv"

# Read the CSV file into a DataFrame
df = pd.read_csv(file_path)

# Select only the required columns
selected_columns = df[['WWID', 'Email', 'Status', 'Respondent']]

# Filter rows where Status is "Waiting" and Respondent is True
filtered_df = selected_columns[(selected_columns['Status'] == 'Waiting') & (selected_columns['Respondent'] == True)]

# Display the dataframes
print("Full DataFrame with Selected Columns:")
print(selected_columns)
print("\nFiltered DataFrame with Status 'Waiting' and Respondent 'True':")
print(filtered_df)

# Save the filtered dataframe as a separate file if needed
filtered_file_path = r"Python Workspace\NexThink Project\Filtered Participants\Filtered_Waiting_Participants.csv"
filtered_df.to_csv(filtered_file_path, index=False)
print(f"\nFiltered waiting participants saved to {filtered_file_path}")
