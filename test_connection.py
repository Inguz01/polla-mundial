from database.google_sheets import connect

db = connect()

sheet = db.worksheet("usuarios")

data = sheet.get_all_records()

print(data)