"""Fetch and save the full services.xml, then parse all services."""
import requests
import datetime
import urllib3
import xml.etree.ElementTree as ET
import json

urllib3.disable_warnings()

USER  = "enzo.pmoreira@agorainvestimentos.com.br"
EPROM = "00-05-9A-3C-7A-00"
TOKEN = "49bc73ce0fcb90a4674e0fb8f91031bb8f012314"
UID   = "623247"


def auth():
    t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return dict(S="AETPHTML", O="BC", E=EPROM, U=USER, T=t, K=TOKEN)


s = requests.Session()
s.headers["User-Agent"] = "bcsys32/7.0"

# Fetch full services.xml
r = s.get("http://cp.ae.com.br:44780/aeterminal/services.xml",
          params=auth(), timeout=15, verify=False)
xml_text = r.text

# Save raw
with open("docs/services.xml", "w", encoding="utf-8") as f:
    f.write(xml_text)
print(f"Saved {len(xml_text)} chars to docs/services.xml")

# Parse services
root = ET.fromstring(xml_text)
services = root.findall(".//service")
print(f"\nTotal services: {len(services)}")

# Organize by protocol
by_proto = {}
for svc in services:
    sid   = svc.get("id")
    name  = (svc.findtext("name") or "").strip()
    proto = (svc.findtext("protocol") or "").strip()
    url   = (svc.findtext("url") or "").strip()
    method = (svc.findtext("method") or "GET").strip()
    cached = (svc.findtext("isCached") or "false").strip()
    req_tags  = [t.text for t in svc.findall("requiredTag")]
    opt_tags  = [t.text for t in svc.findall("optionalTag")]
    by_proto.setdefault(proto, []).append({
        "id": sid, "name": name, "url": url, "method": method,
        "cached": cached, "req": req_tags, "opt": opt_tags
    })

# Print all services
all_svcs = []
for proto in sorted(by_proto):
    print(f"\n--- Protocol: {proto} ---")
    for svc in by_proto[proto]:
        req_str = ",".join(svc["req"]) if svc["req"] else "-"
        print(f"  [{svc['id']:>3}] {svc['method']:6} {svc['url']}")
        print(f"         name={svc['name']}  req={req_str}")
        all_svcs.append(svc)

# Save parsed list to JSON
with open("docs/services_parsed.json", "w", encoding="utf-8") as f:
    json.dump(by_proto, f, indent=2, ensure_ascii=False)
print("\nSaved docs/services_parsed.json")

# Extract ^(server) paths deduplicated
print("\n=== Unique URL patterns ===")
seen = set()
for svc in all_svcs:
    path = svc["url"].replace("^(server)", "")
    path_base = path.split("^(")[0]
    if path_base not in seen:
        seen.add(path_base)
        print(f"  {path}")
