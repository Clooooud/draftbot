from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from settings import SPREADSHEET_ID

# ==========================================
# CONFIG
# ==========================================

SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ==========================================
# SINGLETON LAZY LOAD
# ==========================================

_sheet = None


def getSheet():
    global _sheet

    if _sheet is None:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

        service = build("sheets", "v4", credentials=credentials)

        _sheet = service.spreadsheets()

    return _sheet


# ==========================================
# UTILITAIRES
# ==========================================

def readCell(sheet_name: str, cell: str):
    """
    Lit une cellule.

    Exemple:
        readCell("Feuille1", "A1")
    """

    sheet = getSheet()

    range_name = f"{sheet_name}!{cell}"

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    values = result.get("values", [])

    if not values:
        return None

    return values[0][0]


def writeCell(sheet_name: str, cell: str, value: str|int):
    """
    Écrit dans une cellule.

    Exemple:
        writeCell("Feuille1", "A1", "Hello")
    """

    sheet = getSheet()

    range_name = f"{sheet_name}!{cell}"

    body = {
        "values": [[value]]
    }

    response = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

    return response

def writeCells(sheet_name: str, start_cell: str, values: list[list[str|int]]):
    """
    Écrit dans une plage de cellules à partir d'une cellule de départ.

    Exemple:
        writeCells("Feuille1", "A1", [["Hello", "World"], ["Foo", "Bar"]])
    """

    sheet = getSheet()

    # Calcul de la plage de cellules à partir de la cellule de départ et des dimensions des valeurs
    start_col = start_cell[0]
    start_row = int(start_cell[1:])
    end_col = chr(ord(start_col) + len(values[0]) - 1)
    end_row = start_row + len(values) - 1
    range_name = f"{sheet_name}!{start_col}{start_row}:{end_col}{end_row}"

    body = {
        "values": values
    }

    response = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

    return response