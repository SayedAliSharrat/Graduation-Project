import sqlite3
from datetime import date

def updateSqliteTable():
    try:
        sqliteConnection = sqlite3.connect('db.sqlite3')
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        today = date.today()
        print(today)
        student_id='IT2A01'
        sql_update_query = """Update info_attendance set status = 0 WHERE student_id = ? AND date = ?"""
        tuple=(student_id,today)
        cursor.execute(sql_update_query,tuple)
        sqliteConnection.commit()
        print("Record Updated successfully ")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")

updateSqliteTable()