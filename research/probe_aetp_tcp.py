"""
probe_aetp_tcp.py
Tenta comunicar diretamente com o ContentProxy via protocolo AETP binário.
Também testa via ApiAETP (https://svc.aebroadcast.com.br/).

Baseado em:
- XOR 0xAE encoding dos arquivos de cache
- TAB como separador de campos
- Formato: fieldID\tvalue\n para cada campo
- Auth: campos 12092(UID), 12093(TOKEN), 12055(timestamp)
"""
import socket
import struct
import datetime
import time
import requests
import urllib3

urllib3.disable_warnings()

USER  = "enzo.pmoreira@agorainvestimentos.com.br"
EPROM = "00-05-9A-3C-7A-00"
TOKEN = "49bc73ce0fcb90a4674e0fb8f91031bb8f012314"
UID   = "623247"
KEY   = 0xAE


def xor_encode(text):
    """Encode text with XOR 0xAE."""
    return bytes(b ^ KEY for b in text.encode("latin-1"))


def xor_decode(data):
    """Decode bytes with XOR 0xAE."""
    return bytes(b ^ KEY for b in data).decode("latin-1", errors="replace")


def make_aetp_request_v1(ativo="PETR4", campos=None):
    """
    Formato hipotético v1: header XOR-encoded TAB-separated.
    Linha 1: campo IDs
    Linha 2: valores (auth + request)
    """
    t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if campos is None:
        campos = [2663, 278, 327, 407, 10066]  # ULT, MAX, MIN, ABE, HOR

    # Auth fields + request fields
    field_ids = [12092, 12093, 12055, 10044] + campos
    header = "\t".join(str(f) for f in field_ids) + "\n"
    # Values for auth + ativo + placeholder per campo
    values = [UID, TOKEN, t, ativo] + [""] * len(campos)
    data_line = "\t".join(values) + "\n"

    return xor_encode(header) + xor_encode(data_line)


def make_aetp_request_v2(ativo="PETR4"):
    """
    Formato hipotético v2: request AETP com cabeçalho de tamanho.
    Baseado no formato observado nos arquivos .dat:
    - Primeiro número = tipo de mensagem
    - Depois campos TAB-separados
    """
    t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # BCH request: tipo 101 hipotético
    msg_type = 101
    fields = f"{msg_type}\t{UID}\t{TOKEN}\t{t}\t{ativo}\tULT,FEC,MAX,MIN,ABE\tD\t100\n"
    return xor_encode(fields)


def make_aetp_request_v3(ativo="PETR4"):
    """
    Formato hipotético v3: similar ao login protocol.
    Baseado nos campos do aetp_17.cfg:
    12055=timestamp, 12092=userID, 12093=token
    """
    t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # Formato INI-like mas XOR encoded
    msg = (
        f"[Request]\r\n"
        f"12092={UID}\r\n"
        f"12093={TOKEN}\r\n"
        f"12055={t}\r\n"
        f"10044={ativo}\r\n"
        f"12056=1\r\n"
        f"CAMPOS=ULT,FEC,MAX,MIN\r\n"
        f"PERIODO=D\r\n"
        f"LINHAS=10\r\n"
    )
    return xor_encode(msg)


print("=" * 65)
print("  ContentProxy TCP/HTTP Protocol Probe")
print("=" * 65)

# ─── 1. TCP raw para porta 44780 ─────────────────────────────────────────────
print("\n=== [1] TCP Raw — cp.ae.com.br:44780 ===")

for version, make_fn in [("v1", make_aetp_request_v1), ("v2", make_aetp_request_v2), ("v3", make_aetp_request_v3)]:
    payload = make_fn()
    print(f"\n  Tentativa {version} (payload={len(payload)} bytes, preview={payload[:20].hex()}):")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect(("cp.ae.com.br", 44780))
        s.send(payload)
        time.sleep(2)
        resp = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resp += chunk
                if len(resp) > 10000:
                    break
        except socket.timeout:
            pass
        s.close()

        if resp:
            print(f"  Response ({len(resp)} bytes):")
            print(f"  Hex: {resp[:40].hex()}")
            print(f"  Decoded: {repr(resp[:200])}")
            # Try XOR decode
            xd = xor_decode(resp)
            print(f"  XOR decoded: {repr(xd[:200])}")
        else:
            print("  No response (connection closed immediately)")
    except Exception as e:
        print(f"  Error: {e}")

# ─── 2. ApiAETP via https://svc.aebroadcast.com.br/ ──────────────────────────
print("\n\n=== [2] ApiAETP — https://svc.aebroadcast.com.br/ ===")

SVC = "https://svc.aebroadcast.com.br"
t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Try different URL patterns from RaloAECLR.dll strings
svc_paths = [
    "/CompanyInfo/QueryCompanys",
    "/CompanyInfo/QueryCompanyData",
    "/SharedInformation/QueryItems",
    "/PermissionManager/GetAEServicesPermissions",
    "/bcsys/proxy",
    "/bcsys.proxy",
    "/aetp",
    "/bc/aetp",
    "/bc",
    "/dados",
]

svc_headers = {
    "User-Agent": "bcsys32/7.0",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "X-AE-User": USER,
    "X-AE-Token": TOKEN,
    "X-AE-UID": UID,
}

body_json = {
    "uid": UID,
    "token": TOKEN,
    "timestamp": t,
    "ativo": "PETR4",
    "campos": ["ULT", "FEC", "MAX", "MIN"],
    "periodo": "D",
    "linhas": 10,
}

for path in svc_paths:
    url = SVC + path
    try:
        r = requests.post(url, json=body_json, headers=svc_headers, timeout=8, verify=False)
        ct = r.headers.get("Content-Type", "")[:50]
        mark = "OK" if r.status_code < 400 else "--"
        print(f"  [{mark}] POST {r.status_code}  {path}")
        if r.status_code != 404:
            print(f"         {ct}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR]      {path}: {e}")

# ─── 3. Enumera sub-paths em /CentralMultimidia/ ─────────────────────────────
print("\n\n=== [3] Sub-paths de /CentralMultimidia/ ===")

BASE_CM = "http://cp.ae.com.br:44780/CentralMultimidia"

def auth():
    t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return dict(S="AETPHTML", O="BC", E=EPROM, U=USER, T=t, K=TOKEN)

s = requests.Session()
s.headers["User-Agent"] = "bcsys32/7.0"

cm_paths = [
    "/",
    "/Default.aspx",
    "/Index.aspx",
    "/noticias.aspx",
    "/Noticias.aspx",
    "/Noticias",
    "/Noticias/",
    "/noticias",
    "/noticias/",
    "/news",
    "/news/",
    "/bctv",
    "/bctv/",
    "/video",
    "/dados",
    "/data",
    "/bc",
    "/api",
    "/api/noticias",
    "/bcnoticias.aspx",
    "/BcNoticias.aspx",
    "/TopNews.aspx",
    "/topnews.aspx",
    "/feeds",
    "/feeds/",
    "/feed",
    "/rss",
    "/cadernos",
]

for path in cm_paths:
    url = BASE_CM + path
    try:
        r = s.get(url, params=auth(), timeout=5, verify=False)
        ct = r.headers.get("Content-Type", "")[:50]
        size = len(r.content)
        mark = "OK" if r.status_code < 400 else "--"
        if r.status_code != 404:
            print(f"  [{mark}] {r.status_code}  {path:35s}  {ct}  ({size} bytes)")
            if r.status_code == 200 and size < 1000:
                print(f"         {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR]     {path}: {e}")
