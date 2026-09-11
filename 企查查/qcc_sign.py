"""
企查查 (qcc.com) 请求头动态加密参数复现
==========================================
加密位置: AJAX请求头中一对动态变化的键值对
算法: HMAC-SHA512 + 字符映射表
来源模块: common.cc3e5823.js → 模块 433912
"""

import hmac
import hashlib
import json
import re
import requests


# ============================================================
# 1. codes 映射表 (common.cc3e5823.js 模块 81511)
# ============================================================
CODES = {
    0: "W", 1: "l", 2: "k", 3: "B", 4: "Q",
    5: "g", 6: "f", 7: "i", 8: "i", 9: "r",
    10: "v", 11: "6", 12: "A", 13: "K", 14: "N",
    15: "k", 16: "4", 17: "L", 18: "1", 19: "8",
}
N = 20


# ============================================================
# 2. charMap 映射函数 (common.cc3e5823.js 模块 503560)
#    输入: 路径字符串
#    逻辑: 路径+路径 → 每个字符 charCodeAt() % 20 → 查表codes
# ============================================================
def char_map(path: str) -> str:
    """将路径通过字符映射表转换为HMAC的key"""
    t = (path + path).lower()
    result = ""
    for c in t:
        idx = ord(c) % N
        result += CODES[idx]
    return result


# ============================================================
# 3. Header Name 生成 (common.cc3e5823.js 模块 36321)
#    公式: HmacSHA512(path + body_json, charMap(path)).substr(8, 20)
# ============================================================
def gen_header_name(path: str, body_json: str) -> str:
    """生成动态header的名称 (20位hex子串)"""
    key = char_map(path)
    msg = (path + body_json).encode("utf-8")
    key_bytes = key.encode("utf-8")
    digest = hmac.new(key_bytes, msg, hashlib.sha512).hexdigest().lower()
    return digest[8:28]


# ============================================================
# 4. Header Value 生成 (common.cc3e5823.js 模块 328323)
#    公式: HmacSHA512(path + "pathString" + body_json + tid, charMap(path))
# ============================================================
def gen_header_value(path: str, body_json: str, tid: str) -> str:
    """生成动态header的值 (完整HMAC-SHA512 hex)"""
    key = char_map(path)
    msg = (path + "pathString" + body_json + tid).encode("utf-8")
    key_bytes = key.encode("utf-8")
    digest = hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()
    return digest


# ============================================================
# 5. 获取 window.tid 和 window.pid (前置请求)
#    来源: 首页HTML中注入的 <script>
#    window.pid='xxx'; window.tid='xxx'
# ============================================================
def get_tid_pid(session: requests.Session, cookies: dict = None) -> dict:
    """
    访问企查查任意页面，从HTML中提取 window.pid 和 window.tid
    返回: {"pid": "xxx", "tid": "xxx"}
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    resp = session.get("https://www.qcc.com/", headers=headers, cookies=cookies)

    pid = re.search(r"window\.pid='([^']+)'", resp.text)
    tid = re.search(r"window\.tid='([^']+)'", resp.text)

    if not pid or not tid:
        raise RuntimeError("无法提取 pid/tid，请检查Cookie或WAF状态")

    return {"pid": pid.group(1), "tid": tid.group(1)}


# ============================================================
# 6. 构造完整请求 (签名 + 发送)
# ============================================================
def build_signed_headers(
    method: str,
    path: str,
    params: dict = None,
    data: dict = None,
    pid: str = "",
    tid: str = "",
) -> dict:
    """
    构造带签名的请求头

    参数:
        method: GET / POST
        path: API路径 (如 /api/search/searchcount)
        params: URL查询参数 (GET用)
        data: 请求体 (POST用)
        pid: window.pid
        tid: window.tid

    返回: 完整的headers字典
    """
    # 构造完整URL路径 (含查询参数)
    full_path = path
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        full_path += ("?" if "?" not in path else "&") + qs
    full_path = full_path.lower()

    # 序列化body
    body_json = ""
    if data:
        body_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).lower()

    # 生成签名header
    header_name = gen_header_name(full_path, body_json)
    header_value = gen_header_value(full_path, body_json, tid)

    headers = {
        header_name: header_value,
        "x-pid": pid,
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://www.qcc.com",
        "referer": "https://www.qcc.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    return headers


# ============================================================
# 7. 完整示例: 搜索企查查
# ============================================================
def demo_search():
    """演示: 搜索 "小米" 并打印签名过程"""

    session = requests.Session()

    # 第一步: 获取 tid 和 pid
    print("[1] 获取 window.tid 和 window.pid ...")
    tokens = get_tid_pid(session)
    pid, tid = tokens["pid"], tokens["tid"]
    print(f"    pid = {pid}")
    print(f"    tid = {tid}")
    print()

    # 第二步: 构造搜索请求
    api_path = "/api/search/searchmulti"
    request_data = {
        "key": "小米",
        "pageIndex": 1,
        "pageSize": 10,
    }

    print("[2] 生成签名 ...")
    headers = build_signed_headers(
        method="POST",
        path=api_path,
        data=request_data,
        pid=pid,
        tid=tid,
    )

    # 打印生成的动态header
    sign_key = [k for k in headers if k.startswith(("x", "a", "b", "c", "d", "e", "f", "g", "h",
                                                     "i", "j", "k", "l", "m", "n", "o", "p")) and len(k) > 15]
    if sign_key:
        print(f"    Header Name  = {sign_key[0]}")
        print(f"    Header Value = {headers[sign_key[0]][:40]}...")
    print()

    # 第三步: 发送请求
    print("[3] 发送请求 ...")
    url = "https://www.qcc.com" + api_path
    resp = session.post(url, json=request_data, headers=headers)

    print(f"    状态码: {resp.status_code}")
    print(f"    响应前200字符: {resp.text[:200]}")
    print()

    return resp


# ============================================================
# 8. 算法验证 (对照已知结果)
# ============================================================
def verify():
    """验证算法正确性"""
    print("=" * 60)
    print("算法验证")
    print("=" * 60)

    # 测试 char_map
    test_path = "/api/search/searchcount"
    km = char_map(test_path)
    print(f"charMap('{test_path}') = {km}")
    print(f"  期望: iLAgiklLN8QiklLN8Q86Lv4iLAgiklLN8QiklLN8Q86Lv4")
    ok = km == "iLAgiklLN8QiklLN8Q86Lv4iLAgiklLN8QiklLN8Q86Lv4"
    print(f"  匹配: {'PASS' if ok else 'FAIL'}")
    print()

    # 测试 header_name
    body_simple = '{"count":true,"filter":"{\\"i\\":[\\"a\\"]}"}.lower'
    hn = gen_header_name(test_path, body_simple)
    print(f"headerName = {hn}")
    print(f"  长度 = {len(hn)} (期望20)")
    print(f"  匹配: {'PASS' if len(hn) == 20 else 'FAIL'}")
    print()


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    verify()
    print()
    print("=" * 60)
    print("实际请求测试")
    print("=" * 60)
    print()
    demo_search()
