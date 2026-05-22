import sqlite3

# Test with parameterized queries
conn = sqlite3.connect(':memory:')
conn.execute("""CREATE VIRTUAL TABLE fts USING fts5(content, title, type, tokenize='unicode61')""")
conn.execute('INSERT INTO fts(rowid, content, title, type) VALUES (?, ?, ?, ?)',
    (1, 'How to use SQL databases', 'Database Guide', 'general'))
conn.execute('INSERT INTO fts(rowid, content, title, type) VALUES (?, ?, ?, ?)',
    (2, '关于SQL查询性能优化', '数据库优化', 'general'))
conn.execute('INSERT INTO fts(rowid, content, title, type) VALUES (?, ?, ?, ?)',
    (3, '使用React框架开发组件', 'React开发', 'general'))
conn.commit()

tests = ['SQL', 'React', 'react', '数据库', '优化', '数', '据', '库', '组件', '开发', 'database', 'Database']
for q in tests:
    try:
        cur = conn.execute("SELECT rowid FROM fts WHERE fts MATCH ?", (q,))
        results = [r[0] for r in cur.fetchall()]
        print(f'  MATCH [{q}]: {results}')
    except Exception as e:
        print(f'  MATCH [{q}] error: {e}')

# Check what tokens are in the index
print("\n--- FTS5 vocab ---")
try:
    conn.execute("CREATE VIRTUAL TABLE fts_vocab USING fts5vocab(fts, 'instance')")
    cur = conn.execute("SELECT term FROM fts_vocab ORDER BY term")
    terms = [r[0] for r in cur.fetchall()]
    print(f'  Terms ({len(terms)}): {terms[:50]}')
except Exception as e:
    print(f'  Vocab error: {e}')

# Check SQLite version
print(f"\n--- SQLite version: {sqlite3.sqlite_version} ---")

conn.close()
