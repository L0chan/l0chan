import re
from pathlib import Path

app_path = Path("backend/app.py")
content = app_path.read_text(encoding="utf-8")

# Fix Register
target_register = """    cursor.execute(\"\"\"
    INSERT INTO users(username,password,role)
    VALUES(?,?,?)
    \"\"\", (username, password, role))"""

replacement_register = """    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    cursor.execute(\"\"\"
    INSERT INTO users(username,password,role)
    VALUES(?,?,?)
    \"\"\", (username, hashed_password, role))"""

content = content.replace(target_register, replacement_register)


# Fix Login
target_login = """    cursor.execute(\"\"\"
    SELECT id, username, role FROM users
    WHERE username=? AND password=?
    \"\"\", (username, password))

    user = cursor.fetchone()

    conn.close()

    if user:

        session["user"] = username
        role = normalize_role(user["role"] if isinstance(user, sqlite3.Row) else user[2])"""

replacement_login = """    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(\"\"\"
    SELECT id, username, password, role FROM users
    WHERE username=?
    \"\"\", (username,))

    user = cursor.fetchone()

    conn.close()

    from werkzeug.security import check_password_hash

    is_valid = False
    if user:
        db_password = user["password"]
        if db_password.startswith("scrypt:") or db_password.startswith("pbkdf2:"):
            is_valid = check_password_hash(db_password, password)
        else:
            is_valid = (db_password == password)

    if is_valid:

        session["user"] = username
        role = normalize_role(user["role"])"""

content = content.replace(target_login, replacement_login)

app_path.write_text(content, encoding="utf-8")
print("Done")
