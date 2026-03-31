import gspread
from google.oauth2.service_account import Credentials
from src.utils.env_data import ENVDATA
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_gspread_client():

    creds_info = {
        "type": ENVDATA.TYPE,
        "project_id": ENVDATA.PROJECT_ID,
        "private_key_id": ENVDATA.PRIVATE_KEY_ID,
        "private_key": ENVDATA.PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": ENVDATA.CLIENT_EMAIL,
        "auth_uri": ENVDATA.AUTH_URI,
        "token_uri": ENVDATA.TOKEN_URI,
        "auth_provider_x509_cert_url": ENVDATA.AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": ENVDATA.CLIENT_X509_CERT_URL
    }

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)

    client = gspread.authorize(credentials)

    return client


def get_sheet():

    client = get_gspread_client()

    spreadsheet = client.open(ENVDATA.SPREADSHEET_NAME)

    sheet = spreadsheet.worksheet(ENVDATA.WORKSHEET_NAME)

    return sheet

def get_all_rows():
    sheet = get_sheet()
    headers = sheet.row_values(1)
    data = sheet.get_all_values()

    all_rows = []

    for i, row in enumerate(data[1:], start=2):
        row_dict = {}

        for j, header in enumerate(headers):
            if j < len(row):
                row_dict[header] = row[j]
            else:
                row_dict[header] = ""

        row_dict["row_number"] = i
        all_rows.append(row_dict)

    return all_rows

def get_mrn_rows(practice_name):
    rows = get_all_rows()

    mrn_data = []

    for row in rows:
        practice = str(row.get("Practice", "")).strip()
        download_flag = str(row.get("Download", "")).strip().upper()
        status = str(row.get("Downloading Status", "")).strip().lower()

        if (
            practice == practice_name and
            download_flag == "YES" and
            status != "file downloaded"
        ):
            mrn = str(row.get("MRN", "")).strip()
            balance = str(row.get("Stmt Balance", "")).strip()  
            row_number = row["row_number"]

            if mrn:
                mrn_data.append({
                    "mrn": mrn,
                    "balance": balance,
                    "row": row_number
                })

    return mrn_data

def update_download_status(row: int, status: str = "No"):
    try:
        sheet = get_sheet()

        # Clean headers (avoid space issues)
        headers = [h.strip() for h in sheet.row_values(1)]

        if "Downloading Status" not in headers:
            raise Exception("Column 'Downloading Status' not found")

        status_col = headers.index("Downloading Status") + 1
        download_col = headers.index("Download") + 1

        sheet.update_cell(row, status_col, status)

        if status in ["File Downloaded", "Balance not matching"]:
             sheet.update_cell(row, download_col, "No")

        logger.info(f"Row {row} updated - Status: {status}, Download handled")

    except Exception as e:
        logger.error(f" Failed to update row {row}: {e}")


async def process_practice(row_data):
    # Example dummy logic (replace with real)
    if "download" in row_data.lower():
        return "File Downloaded"
    elif "mismatch" in row_data.lower():
        return "Balance not matching"
    else:
        return "Skipped"


# 🔹 Main workflow loop
async def process_all_rows(rows):
    """
    rows = list of row data from sheet
    """

    for i, row in enumerate(rows):
        row_number = i + 2  # because row 1 = header

        try:
            logger.info(f" Processing row {row_number}")

            result = await process_practice(row)

            logger.info(f"Result for row {row_number}: {result}")

            #  ONLY update for these two cases
            if result and result.strip().lower() in [
                "file downloaded",
                "balance not matching",
            ]:
                update_download_status(row_number, result)

            #  Do nothing for skipped / errors

        except Exception as e:
            logger.error(f" Error processing row {row_number}: {e}")


def get_practices_to_run():
    rows = get_all_rows()  # your existing sheet reader

    practices = set()

    for row in rows:
        practice = str(row.get("Practice", "")).strip()
        download_flag = str(row.get("Download", "")).strip().upper()

        if download_flag == "YES" and practice:
            practices.add(practice)

    return list(practices)    