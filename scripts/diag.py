import httpx, asyncio

async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get("http://127.0.0.1:8000/api/ros/devices")
        devs = r.json()
        # 找 8728 端口的设备
        for d in devs:
            if d['port'] == 8728:
                print(f"Found API device: {d['id']} {d['host']}:{d['port']}")
                # 测试连接
                r2 = await c.get(f"http://127.0.0.1:8000/api/ros/test?host={d['host']}&port={d['port']}&username={d['username']}&password=&use_ssl={d['use_ssl']}")
                print(f"Test connect: {r2.status_code} {r2.text[:300]}")
                
                # 测试 proxy interface
                r3 = await c.get(f"http://127.0.0.1:8000/api/ros/proxy?device_id={d['id']}&path=interface")
                print(f"\nProxy interface: {r3.status_code} {r3.text[:500]}")

asyncio.run(main())
