import urllib.request
import json

BASE = "http://127.0.0.1:8000/api"

def test_api(name, url):
    try:
        r = urllib.request.urlopen(url)
        d = json.loads(r.read())
        print(f"  {name}: OK")
        return d
    except urllib.error.HTTPError as e:
        print(f"  {name}: FAIL {e.code} - {json.loads(e.read()).get('detail', '')}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

print("=== 后端工具 API 测试 ===")
test_api("ping", f"{BASE}/tools/ping?host=127.0.0.1&count=2")
test_api("dns", f"{BASE}/tools/dns?domain=baidu.com&record_type=A")
test_api("subnet-split", f"{BASE}/tools/subnet/split?network=192.168.1.0&prefix=24&new_prefix=26")
