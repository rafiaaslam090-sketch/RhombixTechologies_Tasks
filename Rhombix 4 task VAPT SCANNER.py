

import socket
import sqlite3
import threading
import time
import requests
from flask import Flask, request, make_response
from datetime import datetime

#  PART 1: The Vulnerable Target App

app = Flask(__name__)
DB = "test_users.db"


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("CREATE TABLE users (id INTEGER, username TEXT, password TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'admin123')")
    conn.commit()
    conn.close()


@app.route("/login")
def login():
    # VULNERABLE: raw string concatenation -> SQL Injection
    # ALSO VULNERABLE: weak default credentials -> Broken Authentication
    username = request.args.get("username", "")
    password = request.args.get("password", "")
    conn = sqlite3.connect(DB)
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    try:
        result = conn.execute(query).fetchall()
    except sqlite3.OperationalError as e:
        return f"SQL error occurred: {e}", 500
    conn.close()
    if result:
        return f"Welcome {username}! Login successful."
    return "Invalid login.", 401


@app.route("/search")
def search():
    # VULNERABLE: reflects input -> Reflected XSS
    term = request.args.get("q", "")
    return f"<html><body>Search results for: {term}</body></html>"


@app.route("/")
def home():
    resp = make_response("<h1>Test Shop App</h1><p>Server: TestApp/1.0</p>")
    resp.headers["Server"] = "TestApp/1.0 (Werkzeug)"
    return resp  # deliberately missing security headers


def run_server():
    init_db()
    app.run(port=5000, debug=False, use_reloader=False)


# PART 2: Information Gathering (Nmap-style)

TARGET_HOST = "127.0.0.1"
TARGET = f"http://{TARGET_HOST}:5000"
COMMON_PORTS = [21, 22, 80, 443, 3306, 5000, 8080]


def scan_ports():
    open_ports = []
    for port in COMMON_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex((TARGET_HOST, port)) == 0:
            open_ports.append(port)
        s.close()
    return open_ports


def grab_banner():
    try:
        r = requests.get(TARGET, timeout=5)
        return r.headers.get("Server", "Unknown")
    except requests.RequestException:
        return "Unable to connect"


# PART 3: Vulnerability Scanning

SQLI_PAYLOADS = ["'", "' OR '1'='1", "' OR '1'='1' -- ", "' AND '1'='2"]
SQL_ERROR_SIGNATURES = ["sql error", "sqlite3.operationalerror", "syntax error"]
XSS_PAYLOAD = "<script>alert('VAPT_TEST')</script>"
SECURITY_HEADERS = [
    "Content-Security-Policy", "X-Frame-Options",
    "X-Content-Type-Options", "Strict-Transport-Security",
]
DEFAULT_CREDS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "admin123"),
    ("root", "root"), ("test", "test"),
]
REPORT_FILE = "vapt_report.txt"


def test_sql_injection():
    findings = []
    for payload in SQLI_PAYLOADS:
        r = requests.get(f"{TARGET}/login", params={"username": payload, "password": "x"}, timeout=5)
        body = r.text.lower()
        for sig in SQL_ERROR_SIGNATURES:
            if sig in body:
                findings.append({"payload": payload, "evidence": sig})
                break
    return findings


def test_xss():
    r = requests.get(f"{TARGET}/search", params={"q": XSS_PAYLOAD}, timeout=5)
    return [{"reflected": True}] if XSS_PAYLOAD in r.text else []


def test_broken_auth():
    findings = []
    for user, pwd in DEFAULT_CREDS:
        r = requests.get(f"{TARGET}/login", params={"username": user, "password": pwd}, timeout=5)
        if "successful" in r.text.lower():
            findings.append({"username": user, "password": pwd})
    return findings


def check_security_headers():
    r = requests.get(TARGET, timeout=5)
    return [h for h in SECURITY_HEADERS if h not in r.headers]


#  PART 4: Professional Report

def build_report(open_ports, banner, sqli, xss, auth, missing_headers):
    L = []
    L.append("=" * 62)
    L.append("VULNERABILITY ASSESSMENT & PENETRATION TEST REPORT")
    L.append(f"Target: {TARGET}")
    L.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    L.append("=" * 62)

    L.append("\n[STAGE 1] INFORMATION GATHERING")
    L.append(f"Open ports: {', '.join(map(str, open_ports)) if open_ports else 'None'}")
    L.append(f"Server banner: {banner}")

    L.append("\n[STAGE 2] SQL INJECTION - /login")
    if sqli:
        L.append("Status: VULNERABLE | Risk: HIGH")
        L.append(f"Reproduce: GET /login?username={sqli[0]['payload']}&password=x")
        L.append(f"Evidence: server returned '{sqli[0]['evidence']}'")
        L.append("Fix: Use parameterized queries, never concatenate raw input into SQL.")
    else:
        L.append("Status: Not detected")

    L.append("\n[STAGE 3] REFLECTED XSS - /search")
    if xss:
        L.append("Status: VULNERABLE | Risk: MEDIUM-HIGH")
        L.append(f"Reproduce: GET /search?q={XSS_PAYLOAD}")
        L.append("Fix: Escape/encode user input before rendering in HTML.")
    else:
        L.append("Status: Not detected")

    L.append("\n[STAGE 4] BROKEN AUTHENTICATION - /login")
    if auth:
        L.append("Status: VULNERABLE | Risk: HIGH")
        for a in auth:
            L.append(f"  Valid weak credentials found: {a['username']} / {a['password']}")
        L.append("Fix: Enforce strong password policy, remove default accounts, add lockout.")
    else:
        L.append("Status: No default credentials worked")

    L.append("\n[STAGE 5] MISSING SECURITY HEADERS - /")
    if missing_headers:
        L.append("Status: VULNERABLE | Risk: LOW-MEDIUM")
        for h in missing_headers:
            L.append(f"  Missing: {h}")
        L.append("Fix: Configure server/app to send these headers on every response.")
    else:
        L.append("Status: All headers present")

    L.append("\n" + "=" * 62)
    return "\n".join(L)


def main():
    print("[*] Starting local test server ...")
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1.5)

    print("[*] Stage 1: Information gathering (port scan + banner) ...")
    open_ports = scan_ports()
    banner = grab_banner()

    print("[*] Stage 2: Testing SQL Injection ...")
    sqli = test_sql_injection()

    print("[*] Stage 3: Testing Reflected XSS ...")
    xss = test_xss()

    print("[*] Stage 4: Testing Broken Authentication ...")
    auth = test_broken_auth()

    print("[*] Stage 5: Checking security headers ...")
    missing_headers = check_security_headers()

    report = build_report(open_ports, banner, sqli, xss, auth, missing_headers)
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    print("\n" + report)
    print(f"\n[+] Report saved to {REPORT_FILE}")
    print("[*] Done. Press Ctrl+C to exit.")


if __name__ == "__main__":
    main()
    while True:
        time.sleep(1)
