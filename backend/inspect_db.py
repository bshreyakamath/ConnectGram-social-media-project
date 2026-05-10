import sqlite3

def inspect_all():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']

    if not tables:
        print("The database is empty! No tables found.")
        return

    print("="*60)
    print("      CONNECTGRAM DATABASE OVERVIEW")
    print("="*60)

    for table in tables:
        print(f"\n[ TABLE: {table.upper()} ]")
        
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        print(" | ".join(columns))
        print("-" * (len(" | ".join(columns)) + 2))

        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if not rows:
            print("(No data in this table yet)")
        else:
            for row in rows:
                print(" | ".join(map(str, row)))
        
        print("\n" + "="*30)

    conn.close()

if __name__ == "__main__":
    inspect_all()