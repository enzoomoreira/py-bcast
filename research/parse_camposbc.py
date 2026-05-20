"""
Parse camposbc.tab to extract complete field mapping:
BC_ATTRIB <-> AETP_ATTRIB <-> DDE_KEY <-> description
"""
import csv
import io

path = r"C:\Users\i455561\AppData\Roaming\Agencia Estado\Broadcast\DataFiles\camposbc.tab"
data = open(path, "rb").read()
text = data.decode("latin-1", errors="replace")

reader = csv.reader(io.StringIO(text), delimiter=";")
rows = list(reader)
header = rows[0]
print(f"Header ({len(header)} columns): {header}")
print(f"Total rows: {len(rows) - 1}")
print()

# Parse all fields
fields = []
for row in rows[1:]:
    if len(row) >= 9:
        bc_id = row[0].strip()
        aetp_id = row[1].strip()
        key = row[2].strip()
        alias1 = row[3].strip()
        alias2 = row[4].strip()
        short_desc = row[5].strip()
        description = row[6].strip()
        panel = row[7].strip()
        ftype = row[8].strip()
        fields.append({
            "bc_id": bc_id,
            "aetp_id": aetp_id,
            "key": key,
            "alias1": alias1,
            "alias2": alias2,
            "short_desc": short_desc,
            "description": description,
            "panel": panel,
            "type": ftype,
        })

# Print summary
print(f"{'BC':>5}  {'AETP':>7}  {'KEY':<12}  {'TYPE':<5}  {'DESCRIPTION'}")
print("-" * 80)
for f in fields[:100]:
    print(f"  {f['bc_id']:>5}  {f['aetp_id']:>7}  {f['key']:<12}  {f['type']:<5}  {f['description']}")

# Statistics
types = {}
for f in fields:
    t = f["type"]
    types[t] = types.get(t, 0) + 1
print(f"\n\nField type distribution:")
for t, count in sorted(types.items()):
    print(f"  {t}: {count}")

print(f"\nTotal fields: {len(fields)}")

# Find fields relevant to BCH (historical data)
print("\n\nFields with 'hist' or 'fechamento' in description:")
for f in fields:
    desc = f["description"].lower()
    if any(kw in desc for kw in ["hist", "fech", "anterior", "1 sem", "mês", "ano", "30 dia", "12 mes", "52 sem"]):
        print(f"  {f['bc_id']:>5}  {f['aetp_id']:>7}  {f['key']:<10}  {f['description']}")
