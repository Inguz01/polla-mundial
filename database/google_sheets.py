import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "data/credentials.json",
        scope
    )

    client = gspread.authorize(creds)

    return client.open("polla_mundial")