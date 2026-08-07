import sqlite3

conn = sqlite3.connect('data/institutions.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [r[0] for r in cursor.fetchall()])

try:
    cursor.execute('SELECT COUNT(*) FROM institutions')
    print('Institutions:', cursor.fetchone()[0])
except Exception as e:
    print('No institutions table:', e)

try:
    cursor.execute('SELECT COUNT(*) FROM crawl_logs')
    print('Crawl logs:', cursor.fetchone()[0])
except Exception as e:
    print('No crawl_logs table:', e)

try:
    cursor.execute('SELECT * FROM crawl_runs LIMIT 5')
    print('Crawl runs:', [r for r in cursor.fetchall()])
except Exception as e:
    print('No crawl_runs table:', e)

conn.close()
