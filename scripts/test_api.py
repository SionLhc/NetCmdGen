import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
from app.api.ros_api import api_select, api_get_system

host = '172.29.254.254'
port = 8728
user = 'admin'
pwd = 'admin'

try:
    # 测试系统信息
    info = api_get_system(host, port, user, pwd)
    print('=== System Info ===')
    print(info)
    
    # 测试多个菜单
    for menu in ['interface', 'ip/address', 'ip/dns', 'ip/route', 'ip/service']:
        try:
            data = api_select(host, port, user, pwd, menu)
            print(f'\n=== {menu} ({len(data)} records) ===')
            for r in data[:3]:
                print(f'  {dict(r)}')
        except Exception as e:
            print(f'\n=== {menu}: ERROR {e}')
except Exception as e:
    print(f'CONNECTION ERROR: {e}')
