# vulnerable_app.py
# WARNING: This file is intentionally broken and insecure. For testing purposes only.

import os
import sys
import pickle
import subprocess
import hashlib
import sqlite3
import yaml
import tempfile
from flask import Flask, request, render_template_string

app = Flask(__name__)

# -------------------------------------------------------
# 1. HARDCODED SECRETS & CREDENTIALS
# -------------------------------------------------------

SECRET_KEY = "supersecretkey123"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DB_PASSWORD = "admin123"
API_TOKEN = "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"

app.config['SECRET_KEY'] = "hardcoded-flask-secret"


# -------------------------------------------------------
# 2. SQL INJECTION
# -------------------------------------------------------

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Direct string interpolation in SQL — classic SQLi
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()

def get_user_by_id(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # f-string SQLi
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchall()


# -------------------------------------------------------
# 3. COMMAND INJECTION
# -------------------------------------------------------

def ping_host(host):
    # shell=True with user input is dangerous
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
    return result.stdout

def list_directory(path):
    # os.system with user input
    os.system("ls " + path)


# -------------------------------------------------------
# 4. INSECURE DESERIALIZATION
# -------------------------------------------------------

def load_user_data(data):
    # pickle.loads on untrusted data allows arbitrary code execution
    return pickle.loads(data)

def load_config(config_bytes):
    # yaml.load without Loader is unsafe
    return yaml.load(config_bytes)


# -------------------------------------------------------
# 5. PATH TRAVERSAL
# -------------------------------------------------------

def read_file(filename):
    # No sanitization — allows reading /etc/passwd etc.
    with open("/var/www/uploads/" + filename, "r") as f:
        return f.read()

def write_file(filename, content):
    path = os.path.join("/var/www/uploads/", filename)
    with open(path, "w") as f:
        f.write(content)


# -------------------------------------------------------
# 6. XSS — SERVER-SIDE TEMPLATE INJECTION (SSTI)
# -------------------------------------------------------

@app.route("/hello")
def hello():
    name = request.args.get("name", "World")
    # render_template_string with user input = SSTI
    return render_template_string(f"<h1>Hello, {name}!</h1>")

@app.route("/search")
def search():
    query = request.args.get("q", "")
    # Directly reflecting user input without escaping
    return f"<p>Results for: {query}</p>"


# -------------------------------------------------------
# 7. WEAK CRYPTOGRAPHY
# -------------------------------------------------------

def hash_password(password):
    # MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()

def hash_password_v2(password):
    # SHA1 is also considered weak for passwords
    return hashlib.sha1(password.encode()).hexdigest()

def encrypt_data(data):
    # Using a hardcoded key and no IV — insecure
    key = b"1234567890abcdef"
    from Crypto.Cipher import AES
    cipher = AES.new(key, AES.MODE_ECB)  # ECB mode is insecure
    return cipher.encrypt(data)


# -------------------------------------------------------
# 8. INSECURE RANDOM
# -------------------------------------------------------

import random

def generate_token():
    # random is not cryptographically secure
    return str(random.randint(100000, 999999))

def generate_session_id():
    return hex(random.getrandbits(64))


# -------------------------------------------------------
# 9. UNSAFE REDIRECTS & HTTP
# -------------------------------------------------------

@app.route("/redirect")
def unsafe_redirect():
    from flask import redirect
    url = request.args.get("url")
    # Open redirect — no validation of destination
    return redirect(url)


# -------------------------------------------------------
# 10. INSECURE FILE UPLOAD
# -------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload_file():
    f = request.files["file"]
    # No file type validation whatsoever
    f.save("/var/www/uploads/" + f.filename)
    return "Uploaded"


# -------------------------------------------------------
# 11. VERBOSE ERROR DISCLOSURE
# -------------------------------------------------------

@app.route("/user/<user_id>")
def get_user_route(user_id):
    try:
        result = get_user_by_id(user_id)
        return str(result)
    except Exception as e:
        # Leaking full exception details to the client
        return f"Error: {str(e)}, Query: SELECT * FROM users WHERE id = {user_id}", 500


# -------------------------------------------------------
# 12. DEBUG MODE ENABLED
# -------------------------------------------------------

@app.route("/debug")
def debug_info():
    return {
        "env": dict(os.environ),      # Exposing all env vars
        "args": sys.argv,
        "cwd": os.getcwd(),
    }


# -------------------------------------------------------
# 13. INSECURE TEMP FILES
# -------------------------------------------------------

def write_temp_data(data):
    # predictable temp file name
    tmp_path = "/tmp/app_data.txt"
    with open(tmp_path, "w") as f:
        f.write(data)

def safe_temp_file(data):
    # mktemp is deprecated and insecure (race condition)
    tmp = tempfile.mktemp()
    with open(tmp, "w") as f:
        f.write(data)


# -------------------------------------------------------
# 14. EXEC / EVAL INJECTION
# -------------------------------------------------------

@app.route("/calc")
def calc():
    expr = request.args.get("expr", "")
    # eval on user input = arbitrary code execution
    result = eval(expr)
    return str(result)

@app.route("/run")
def run_code():
    code = request.args.get("code", "")
    # exec is even worse
    exec(code)
    return "Done"


# -------------------------------------------------------
# 15. MISSING AUTH & BROKEN ACCESS CONTROL
# -------------------------------------------------------

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    # No authentication or authorization check at all
    user_id = request.form.get("user_id")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()
    return "Deleted"


# -------------------------------------------------------
# 16. LOGGING SENSITIVE DATA
# -------------------------------------------------------

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def authenticate(username, password):
    # Logging credentials in plaintext
    logger.debug(f"Login attempt: username={username}, password={password}")
    return username == "admin" and password == DB_PASSWORD


# -------------------------------------------------------
# ENTRY POINT — debug=True in production
# -------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
