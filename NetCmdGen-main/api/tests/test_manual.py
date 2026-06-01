import urllib.request
import json

BASE = "http://127.0.0.1:8000/api"

# 1. vendors
r = urllib.request.urlopen(f"{BASE}/vendors")
v = json.loads(r.read())
print(f"=== Vendors ({len(v['vendors'])}) ===")
for vv in v["vendors"]:
    print(f"  {vv['code']:10s}  {vv['name']:20s}  features={vv['features']}")

# 2. manual search
r = urllib.request.urlopen(f"{BASE}/manual/huawei?keyword=SSH")
m = json.loads(r.read())
print(f"\n=== manual huawei keyword=SSH ({m['total']} results) ===")
for it in m["items"][:3]:
    print(f"  {it['name']:20s}  {it['command'][:60]}")

# 3. manual tree
r = urllib.request.urlopen(f"{BASE}/manual/h3c/tree")
t = json.loads(r.read())
print(f"\n=== manual h3c tree top-level keys ===")
print(f"  {list(t['tree'].keys())}")

print("\nOK - all manual endpoints working")
