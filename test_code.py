# This is intentionally insecure test code for Semgrep scanning

import os
import sqlite3

def insecure_eval(user_input):
    # BAD: eval on untrusted input
    eval(user_input)

def hardcoded_secret():
    # BAD: Hardcoded API key
    API_KEY = "AKIA1234567890EXAMPLE"
    print("Using API key:", API_KEY)

def sql_injection(user_input):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # BAD: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    cursor.execute(query)
    conn.close()

if __name__ == "__main__":
    insecure_eval("print('Hello from eval!')")
    hardcoded_secret()
    sql_injection("admin' OR '1'='1")
How to Scan with Semgrep
Bash

Copy code
# Install Semgrep if not already installed
pip install semgrep

# Run a basic scan with built-in security rules
semgrep --config=p/ci test_insecure.py