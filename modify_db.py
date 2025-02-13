import sqlite3

def updateSqliteTable():
    try:
        sqliteConnection = sqlite3.connect('db.sqlite3')
        cursor = sqliteConnection.cursor()
        # cursor.execute("SELECT * FROM info_attendance")
        # rows = cursor.fetchall()
        print("Connected to SQLite")
        # for row in rows:
        #   print(row)
        sql_update_query = """Update info_attendance set status = 1 WHERE student_id = 'IT2A01' AND date = '2025-01-06';"""
        cursor.execute(sql_update_query)
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