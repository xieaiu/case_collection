import execjs
import json
import requests

with open('qcc.js','r',encoding='utf-8') as f:
    js_code = f.read()
ctx = execjs.compile(js_code)

page = 1
headers_info = ctx.call('get_pageinfo',page)
print(headers_info)

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/json",
    headers_info['key']: headers_info['value'],
    "origin": "https://www.qcc.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.qcc.com/web/search?key=%E5%B0%8F%E7%B1%B3",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"99\", \"Google Chrome\";v=\"151\", \"Chromium\";v=\"151\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "x-pid": "e433881c144eb274bc10020728d4bbf2",
    "x-requested-with": "XMLHttpRequest"
}
# 登录态 Cookie 已脱敏，运行时请从浏览器登录后复制真实值。
cookies = {
    "QCCSESSID": "",
    "qcc_did": "",
    "UM_distinctid": "",
    "_c_WBKFRo": "",
    "_nb_ioWEgULi": "",
    "acw_tc": "",
    "CNZZDATA1254842228": "",
}
url = 'https://www.qcc.com/api/search/searchMulti'
data = json.dumps({"searchKey": "小米", "pageIndex": page, "pageSize": 20}).encode('utf-8')
response = requests.post(url, headers=headers, cookies=cookies, data=data)

print(response.text)
print(response)