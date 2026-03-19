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


def get_mrn_rows():

    sheet = get_sheet()

    headers = sheet.row_values(1)

    try:
          mrn_col = headers.index("MRN") + 1
    except ValueError:
          raise Exception("Column 'MRN' not found in Google Sheet")

    try:
        balance_col = headers.index("Stmt Balance") + 1
    except ValueError:
        raise Exception("Column 'Stmt Balance' not found in Google Sheet")

    rows = sheet.get_all_values()

    mrn_data = []

    for i, row in enumerate(rows[1:], start=2):

        # Ensure row has enough columns
        if len(row) >= max(mrn_col, balance_col):

            mrn = row[mrn_col - 1].strip()
            balance = row[balance_col - 1].strip()

            if mrn:
                mrn_data.append({
                    "mrn": mrn,
                    "balance": balance,
                    "row": i
                })

    return mrn_data


def update_download_status(row, status):

    sheet = get_sheet()

    headers = sheet.row_values(1)

    try:
        status_col = headers.index("Downloading Status") + 1
    except ValueError:
        raise Exception("Column 'Downloading Status' not found")

    sheet.update_cell(row, status_col, status)

    logger.info(f"Updated row {row} with status: {status}")