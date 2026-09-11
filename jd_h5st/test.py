import hashlib
import json
import os
import subprocess
import time

import requests

# 注意：以下 cookie 均为真实登录态，已脱敏为占位符。
# 运行时请从浏览器登录后的 Cookie 中填充，未填充的值使用空字符串。
cookies = {
    '__jdu': '',
    'areaId': '18',
    'shshshfpa': '',
    'shshshfpx': '',
    '__jdv': '',
    'PCSYCityID': 'CN_430000_430100_0',
    'mba_muid': '',
    'wlfstk_smdl': '',
    '3AB9D23F7A4B3C9B': '',
    'TrackID': '',
    'thor': '',
    'light_key': '',
    'pinId': '',
    'pin': '',
    'unick': '',
    'ceshi3.com': '000',
    '_tp': '',
    '_pst': '',
    'ipLoc-djd': '',
    'cid': '9',
    '__jda': '',
    '__jdc': '',
    'flash': '',
    '3AB9D23F7A4B3CSS': '',
    '_gia_d': '1',
    'shshshfpb': '',
    'cn': '0',
    '__jdb': '',
    'sdtoken': '',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'origin': 'https://search.jd.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://search.jd.com/Search?keyword=%E8%A1%A3%E6%9C%8D&enc=utf-8',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    'x-referer-page': 'https://search.jd.com/Search',
    'x-rp-client': 'h5_2.1.0',
    # 'cookie': '<登录后从浏览器复制的完整 Cookie 串>'（已脱敏，勿提交真实值）
}

API_URL = 'https://api.m.jd.com/api'
SIGNER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'env', 'sign.js'))
NODE_PATH = os.getenv('JD_NODE', 'node')

search_body = {
    'ad_ids': '292:6',
    'xtest': 'new_search',
    'ec': 'utf-8',
    'area': '18',
    'page': '1',
    'simpleSearch': '0',
}


def sign_query(body_text: str, request_t: int) -> dict:
    sign_input = {
        'appid': 'search-pc-java',
        'functionId': 'pc_search_adv_Search',
        'client': 'pc',
        'clientVersion': '1.0.0',
        't': request_t,
        'body': hashlib.sha256(body_text.encode('utf-8')).hexdigest(),
    }
    try:
        completed = subprocess.run(
            [NODE_PATH, SIGNER_PATH, json.dumps(sign_input, ensure_ascii=False)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
            check=True,
        )
        payload = json.loads(completed.stdout)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f'找不到 Node.js：{NODE_PATH}；请安装 Node.js 或设置 JD_NODE 为 node.exe 的完整路径'
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or '').strip()
        raise RuntimeError(f'本地签名脚本执行失败：{detail}') from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('本地签名脚本执行超时') from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError('本地签名脚本返回的不是 JSON') from exc

    signed = payload.get('output') or {}
    if not signed.get('h5st'):
        raise RuntimeError(f'本地签名失败：{payload}')
    return signed


body_text = json.dumps(search_body, ensure_ascii=False, separators=(',', ':'))
request_t = int(time.time() * 1000)
signed = sign_query(body_text, request_t)

# x-api-eid-token 是页面登录/设备态产生的 token，不由 ParamsSign 生成。
# api_eid_token = cookies.get('3AB9D23F7A4B3CSS')
# 已脱敏：运行时请用浏览器动态获取的真实值替换。
api_eid_token = ''
if not api_eid_token:
    raise RuntimeError('cookies 中缺少 3AB9D23F7A4B3CSS，无法设置 x-api-eid-token')

params = [
    ('appid', 'search-pc-java'),
    ('t', request_t),
    ('client', 'pc'),
    ('clientVersion', '1.0.0'),
    ('cthr', '1'),
    ('uuid', cookies['__jdu']),
    ('loginType', '3'),
    ('keyword', '衣服'),
    ('functionId', 'pc_search_adv_Search'),
    ('body', body_text),
    ('x-api-eid-token', api_eid_token),
    ('h5st', signed['h5st']),
    ('t', request_t + 1),
]

response = requests.get(
    API_URL,
    params=params,
    cookies=cookies,
    headers=headers,
    timeout=30,
)
print(response.text)
print(response)
