import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(dbname="postgres", user="postgres", password="1", host="127.0.0.1", port=5432)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_roles WHERE rolname='warehouse_user';")
if not cur.fetchone():
    cur.execute("CREATE ROLE warehouse_user WITH LOGIN PASSWORD 'warehouse_password' CREATEDB;")
    print("warehouse_user role created")
else:
    cur.execute("ALTER ROLE warehouse_user WITH PASSWORD 'warehouse_password' CREATEDB;")
    print("warehouse_user role updated")

cur.execute("SELECT 1 FROM pg_database WHERE datname='warehouse_db';")
if not cur.fetchone():
    cur.execute("CREATE DATABASE warehouse_db OWNER warehouse_user;")
    print("warehouse_db created")
else:
    print("warehouse_db already exists")

cur.execute("SELECT 1 FROM pg_database WHERE datname='warehouse_test_db';")
if not cur.fetchone():
    cur.execute("CREATE DATABASE warehouse_test_db OWNER warehouse_user;")
    print("warehouse_test_db created")
else:
    print("warehouse_test_db already exists")

cur.execute("GRANT ALL PRIVILEGES ON DATABASE warehouse_db TO warehouse_user;")
cur.execute("GRANT ALL PRIVILEGES ON DATABASE warehouse_test_db TO warehouse_user;")
cur.close()
conn.close()
print("PostgreSQL setup completed successfully!")
