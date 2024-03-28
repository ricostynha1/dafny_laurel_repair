import csv
from datetime import datetime
import gspread
import yaml

SPREADSHEET_NAME = "results_dafny_repair"


def upload_results(project_name, csv_file):
    with open("secrets.yaml", "r") as f:
        secrets = yaml.safe_load(f)
    gc = gspread.service_account(filename=secrets["GOOGLE_OAUTH_JSON"])

    spreadsheet = gc.open(SPREADSHEET_NAME)

    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    new_worksheet_name = f"{project_name}-{timestamp}"

    with open(csv_file, "r") as file:
        csv_reader = csv.reader(file)
        csv_data = list(csv_reader)
        num_cols = len(csv_data[0]) if csv_data else 0
        num_rows = len(csv_data)

        worksheet = spreadsheet.add_worksheet(
            title=new_worksheet_name, rows=num_rows, cols=num_cols
        )
        worksheet.clear()
        worksheet.insert_rows(csv_data)
    print(
        f"CSV data uploaded to a new worksheet '{new_worksheet_name}' in Google Sheets successfully!"
    )
