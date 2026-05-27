"""
Generate comprehensive docs/legacy/fields.md from camposbc.tab.
"""

import csv
import io
from pathlib import Path

path = (
    r"C:\Users\i455561\AppData\Roaming\Agencia Estado\Broadcast\DataFiles\camposbc.tab"
)
data = open(path, "rb").read()
text = data.decode("latin-1", errors="replace")

reader = csv.reader(io.StringIO(text), delimiter=";")
rows = list(reader)

fields = []
for row in rows[1:]:
    if len(row) >= 9:
        fields.append(
            {
                "bc_id": row[0].strip(),
                "aetp_id": row[1].strip(),
                "key": row[2].strip(),
                "alias1": row[3].strip(),
                "alias2": row[4].strip(),
                "short_desc": row[5].strip(),
                "description": row[6].strip(),
                "panel": row[7].strip(),
                "type": row[8].strip(),
            }
        )

type_names = {
    "F": "Float (price/value)",
    "V": "Variation (% or abs change)",
    "I": "Integer",
    "Q": "Quantity",
    "T": "Text",
    "H": "Time (HH:MM:SS)",
    "D": "Date",
    "O": "Offset/Nominal change",
    "U": "UTC Time",
    "d": "Date (alt format)",
    "": "Unknown",
}

out = []
out.append("# Broadcast+ Field Reference\n")
out.append(
    "Source: `camposbc.tab` (decoded from `C:\\Users\\...\\DataFiles\\camposbc.tab`)\n"
)
out.append("\n")
out.append("## Column Meanings\n")
out.append("- **BC_ID**: Internal field index (0-based)\n")
out.append("- **AETP_ID**: AETP binary protocol attribute number\n")
out.append(
    "- **KEY**: DDE field name (used in `=BC(ticker, KEY)` and subscription item `TICKER.KEY`)\n"
)
out.append(
    "- **TYPE**: Data type (F=Float, V=Variation, I=Integer, Q=Quantity, T=Text, H=Time, D=Date)\n"
)
out.append("- **DESCRIPTION**: Portuguese description\n")
out.append("\n")
out.append("## Real-Time Fields (DDE: BC/COT, BC/ATIVO)\n")
out.append("\n")
out.append(f"{'BC_ID':>5} | {'AETP_ID':>8} | {'KEY':<14} | {'TYPE':<6} | DESCRIPTION\n")
out.append(f"{'-' * 5}-+-{'-' * 8}-+-{'-' * 14}-+-{'-' * 6}-+-{'-' * 40}\n")

# Group by category
categories = {
    "Price & Quote": list(range(0, 25)),
    "Settlement & Derivatives": list(range(17, 58)),
    "Fixed Income": list(range(58, 100)),
    "Fund Data": list(range(87, 92)),
    "Performance (Variation)": [],
    "Historical Closing": [],
    "Volume Averages": [],
    "Fundamentals (Consolidated)": [],
    "Fundamentals (Individual)": [],
    "Market Cap & Valuation": [],
    "Other": [],
}

for f in fields:
    bc = f["bc_id"]
    key = f["key"]
    desc = f["description"].lower()
    if "variação" in desc and ("mês" in desc or "ano" in desc or "sem" in desc):
        categories["Performance (Variation)"].append(int(bc) if bc.isdigit() else -1)
    elif "fechamento há" in desc or "fechamento do" in desc or "fechamento ano" in desc:
        categories["Historical Closing"].append(int(bc) if bc.isdigit() else -1)
    elif "volume médio" in desc:
        categories["Volume Averages"].append(int(bc) if bc.isdigit() else -1)
    elif "acumulado 12 meses consolidado" in desc:
        categories["Fundamentals (Consolidated)"].append(
            int(bc) if bc.isdigit() else -1
        )
    elif "acumulado 12 meses individual" in desc:
        categories["Fundamentals (Individual)"].append(int(bc) if bc.isdigit() else -1)

for f in fields:
    bc = f["bc_id"]
    key = f["key"]
    aetp = f["aetp_id"]
    typ = f["type"]
    desc = f["description"]
    out.append(f"{bc:>5} | {aetp:>8} | {key:<14} | {typ:<6} | {desc}\n")

# Write to file
output_path = Path(__file__).parent.parent / "docs" / "legacy" / "fields.md"
with open(output_path, "w", encoding="utf-8") as fp:
    fp.write("# Broadcast+ Field Reference\n\n")
    fp.write(
        "**Source**: `camposbc.tab` — complete field mapping: BC_ID ↔ AETP_ID ↔ DDE_KEY\n\n"
    )
    fp.write("## Column Meanings\n\n")
    fp.write("| Column | Description |\n|--------|-------------|\n")
    fp.write("| `BC_ID` | Internal field index (0-based) |\n")
    fp.write("| `AETP_ID` | AETP binary protocol attribute number |\n")
    fp.write(
        '| `KEY` | DDE field name — used in `=BC("TICKER", "KEY")` and `TICKER.KEY` |\n'
    )
    fp.write(
        "| `TYPE` | F=Float, V=Variation%, I=Integer, Q=Quantity, T=Text, H=Time, D=Date, O=Offset |\n"
    )
    fp.write("| `DESCRIPTION` | Portuguese description |\n\n")
    fp.write("---\n\n")
    fp.write("## All Fields\n\n")
    fp.write(
        f"{'BC_ID':>5} | {'AETP_ID':>8} | {'KEY':<14} | {'TYPE':<6} | DESCRIPTION\n"
    )
    fp.write(f"{'-' * 5}-+-{'-' * 8}-+-{'-' * 14}-+-{'-' * 6}-+-{'-' * 50}\n")
    for f in fields:
        bc = f["bc_id"]
        aetp = f["aetp_id"]
        key = f["key"]
        typ = f["type"]
        desc = f["description"]
        fp.write(f"{bc:>5} | {aetp:>8} | {key:<14} | {typ:<6} | {desc}\n")
    fp.write(f"\n\n**Total: {len(fields)} fields**\n")

print(f"Written {len(fields)} fields to docs/legacy/fields.md")
