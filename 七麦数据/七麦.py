import execjs
import requests

url = "https://api.qimai.cn/rank/offline"

with open("./七麦.js", "r", encoding="utf-8") as f:
    js = f.read()

ctx = execjs.compile(js)


for page in range(1, 6):
    params = {
        "analysis": ctx.call("pagesource",page),
        "status": "3",
        "date": "2026-08-13",
        "sdate": "2026-08-13",
        "edate": "2026-08-13",
        "country": "cn",
        "genre": "36",
        "option": "4",
        "page": page,
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Origin": "https://www.qimai.cn",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Not=A?Brand\";v=\"99\", \"Google Chrome\";v=\"151\", \"Chromium\";v=\"151\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }

    # 登录态 Cookie 已脱敏，运行时请从浏览器登录后复制真实值。
    cookies = {
        "qm_check": "",
        "PHPSESSID": "",
        "aso_ucenter": "",
        "USERINFO": "",
        "AUTHKEY": "",
        "gr_user_id": "",
        "ada35577182650f1_gr_session_id": "",
        "ada35577182650f1_gr_session_id_sent_vst": "",
        "synct": "",
        "syncd": "",
    }

    response = requests.request(
        "GET",
        url,
        params=params,
        headers=headers,
        cookies=cookies,
    )
    response.encoding = 'utf-8'
    print(response.json())

