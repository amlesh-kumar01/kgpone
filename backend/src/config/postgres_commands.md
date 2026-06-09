# PostgreSQL Cheat Sheet

This file contains commonly used PostgreSQL commands and queries for managing the `kgpone` database locally. You can run these commands either in `pgAdmin` or via the `psql` command-line tool.

## 1. Using the `psql` Command Line
If you have `psql` in your terminal PATH, you can connect to your database using:
```bash
# Connect as default postgres user
psql -U postgres

# Connect directly to the kgpone database
psql -U postgres -d kgpone
```

### Useful `psql` Meta-Commands
Once inside the `psql` terminal, use these shortcuts:
- `\l` : List all databases on the server.
- `\c kgpone` : Connect to the `kgpone` database.
- `\dt` : List all tables in the current database.
- `\d table_name` : Describe the schema (columns, types, foreign keys) of a specific table.
- `\q` : Quit the psql terminal.

---

## 2. Common SQL Queries (Run in pgAdmin or psql)

### Database Management
```sql
-- Create the main database (Run this before starting the FastAPI app for the first time)
CREATE DATABASE kgpone;

-- Drop the database (WARNING: Deletes all data. Cannot drop while connected to it)
DROP DATABASE kgpone;
```

### Checking Tables and Data
```sql
-- View all registered users
SELECT * FROM users;

-- View all uploaded content
SELECT * FROM content;

-- Count how many users exist in the system
SELECT COUNT(*) FROM users;
```

### Troubleshooting & Modifying Data
```sql
-- Manually promote a user to an ADMIN or PUBLISHER
UPDATE users 
SET role = 'ADMIN' 
WHERE email = 'your.email@example.com';

-- Delete a specific user for testing purposes
DELETE FROM users 
WHERE email = 'testuser@example.com';

-- Delete all users (Reset users table)
DELETE FROM users;
```

### Working with Alembic (Future)
Once we set up Alembic for database migrations, you won't need to write `CREATE TABLE` or `ALTER TABLE` manually. SQLAlchemy and Alembic will handle it. However, if you ever need to forcefully wipe the schema and start fresh during local development:
```sql
-- Drop all tables including the Alembic version tracking table
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```
