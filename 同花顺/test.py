import html
import re
import urllib.request
import ssl
import os
from html.parser import HTMLParser
from pathlib import Path

QN_VALUE = 'A__zbdrUqas8EK20DsB0n8bzjtiM5FCVbT5XVpHMmnb0iBGGmbTj1n0I5_ei'
BASE_URL = "https://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/{page}/ajax/1/"
PAGE_START = int(os.environ.get("PAGE_START", "1"))
PAGE_END = int(os.environ.get("PAGE_END", "6"))

# 登录态 Cookie 已脱敏，运行时请从浏览器登录后复制真实值。
COOKIES = {
    "Hm_lvt_9d25c03aef06fec6abea265b79509ba4": "",
    "HMACCOUNT": "",
    "Hm_lvt_6dc19a3987135225beb977a0b9931a25": "",
    "Hm_lpvt_6dc19a3987135225beb977a0b9931a25": "",
    "Hm_lpvt_9d25c03aef06fec6abea265b79509ba4": "",
    "v": QN_VALUE,
}


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("td", "th") and self.cell is not None:
            text = re.sub(r"\s+", " ", html.unescape("".join(self.cell))).strip()
            self.row.append(text)
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)
            self.row = []


def fetch_html(page):
    cookie = "; ".join(f"{k}={v}" for k, v in COOKIES.items() if v)
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Referer": "https://q.10jqka.com.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "hexin-v": QN_VALUE,
        "Cookie": cookie,
    }
    url = BASE_URL.format(page=page)
    request = urllib.request.Request(url, headers=headers)
    # 优先使用系统证书；若本机 CA 缺失，使用仅限本次目标请求的兼容上下文。
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=20, context=context) as response:
            raw = response.read()
            content_type = response.headers.get_content_charset()
    except ssl.SSLError as exc:
        print("SSL handshake failed; retrying with compatibility context:", exc)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(request, timeout=20, context=context) as response:
            raw = response.read()
            content_type = response.headers.get_content_charset()
    match = re.search(rb"charset\s*=\s*['\"]?([\w-]+)", raw[:1000], re.I)
    encoding = content_type or (match.group(1).decode("ascii", "ignore") if match else "utf-8")
    if encoding.lower().replace("-", "") in ("iso88591", "latin1", "ascii"):
        encoding = "gb18030"
    for candidate in (encoding, "utf-8", "gb18030"):
        try:
            return raw.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def main():
    if not QN_VALUE:
        print("QN_VALUE 为空，等待浏览器生成参数")
        return
    try:
        all_lines = []
        for page in range(PAGE_START, PAGE_END + 1):
            try:
                source = fetch_html(page)
            except Exception as exc:
                print(f"page={page} request failed:", repr(exc))
                continue
            parser = TableParser()
            parser.feed(source)
            lines = ["\t".join(cell for cell in row if cell) for row in parser.rows]
            if not lines:
                lines = [re.sub(r"\s+", " ", html.unescape(x)).strip()
                         for x in re.findall(r"<[^>]+>(.*?)</[^>]+>", source, re.S)]
                lines = [x for x in lines if x]
            all_lines.append(f"[page={page}]")
            all_lines.extend(lines)
    except Exception as exc:
        print("HTML parse failed:", repr(exc))
        return
    output = "\n".join(all_lines)
    Path(__file__).with_name("html_parameters.txt").write_text(output + "\n", encoding="utf-8")
    print(f"HTML parameters, pages {PAGE_START}-{PAGE_END}:")
    print(output)


if __name__ == "__main__":
    main()
