import sqlite3

conn = sqlite3.connect("bb_stats.db")
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM pitching_stats")
print("Pitching rows:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM hitting_stats")
print("Hitting rows:", cur.fetchone()[0])

conn.close()
