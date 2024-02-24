import csv
from datetime import datetime
import gspread
import os

SPREADSHEET_NAME = "results_dafny_repair"


def upload_results(project_name, csv_file):
    gc = gspread.service_account(filename=os.getenv("GOOGLE_OAUTH_JSON"))

    spreadsheet = gc.open(SPREADSHEET_NAME)

    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    new_worksheet_name = f"{project_name}-{timestamp}"
    worksheet = spreadsheet.add_worksheet(
        title=new_worksheet_name, rows=1000, cols=1000
    )

    with open(csv_file, "r") as file:
        csv_reader = csv.reader(file)
        csv_data = list(csv_reader)
        worksheet.clear()
        worksheet.insert_rows(csv_data)
    print(
        f"CSV data uploaded to a new worksheet '{new_worksheet_name}' in Google Sheets successfully!"
    )
