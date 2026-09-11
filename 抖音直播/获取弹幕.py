import argparse
import re
import time

import requests


DEFAULT_ROOM_URL = "https://live.douyin.com/204621511351"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)


def read_varint(data, index):
    value = 0
    shift = 0
    while index < len(data):
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, index
        shift += 7
        if shift >= 70:
            raise ValueError("invalid protobuf varint")
    raise ValueError("truncated protobuf varint")


def iter_fields(data):
    """Yield (field_number, wire_type, value) from a protobuf message."""
    index = 0
    while index < len(data):
        key, index = read_varint(data, index)
        field_number = key >> 3
        wire_type = key & 7
        if field_number == 0:
            raise ValueError("invalid protobuf field number")

        if wire_type == 0:
            value, index = read_varint(data, index)
        elif wire_type == 1:
            end = index + 8
            if end > len(data):
                raise ValueError("truncated protobuf fixed64")
            value = data[index:end]
            index = end
        elif wire_type == 2:
            length, index = read_varint(data, index)
            end = index + length
            if end > len(data):
                raise ValueError("truncated protobuf bytes")
            value = data[index:end]
            index = end
        elif wire_type == 5:
            end = index + 4
            if end > len(data):
                raise ValueError("truncated protobuf fixed32")
            value = data[index:end]
            index = end
        elif wire_type in (3, 4):
            # Unknown groups are not needed by the current response. Skip the
            # group so an unrelated field cannot break the whole poll cycle.
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")

        yield field_number, wire_type, value


def decode_text(value):
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def get_room_context(session, room_url):
    response = session.get(room_url, timeout=30)
    response.raise_for_status()

    room_ids = re.findall(r'\\"roomId\\":\\"(\d+)\\"', response.text)
    if not room_ids:
        raise RuntimeError("无法从直播间页面提取 room_id")

    user_ids = re.findall(r'user_unique_id\\":\\"(\d+)\\"', response.text)
    if not user_ids:
        raise RuntimeError("无法从直播间页面提取 user_unique_id")

    return room_ids[0], user_ids[0]


def parse_chat_message(payload):
    values = {}
    for number, _, value in iter_fields(payload):
        values.setdefault(number, []).append(value)

    user = values.get(2, [b""])[0]
    user_values = {}
    if isinstance(user, bytes):
        for number, _, value in iter_fields(user):
            user_values.setdefault(number, []).append(value)

    return {
        "nickname": decode_text(user_values.get(3, [b""])[0]),
        "content": decode_text(values.get(3, [b""])[0]),
        "raw_payload": payload,
    }


def parse_response(body):
    messages = []
    fields = list(iter_fields(body))
    for number, _, value in fields:
        if number != 1 or not isinstance(value, bytes):
            continue

        message_fields = {}
        for message_number, _, message_value in iter_fields(value):
            message_fields.setdefault(message_number, []).append(message_value)

        method = decode_text(message_fields.get(1, [b""])[0])
        payload = message_fields.get(2, [b""])[0]
        if method == "WebcastChatMessage" and isinstance(payload, bytes):
            messages.append(parse_chat_message(payload))

    cursor = decode_text(next((value for number, _, value in fields if number == 2), b""))
    internal_ext = decode_text(
        next((value for number, _, value in fields if number == 5), b"")
    )
    return messages, cursor, internal_ext


def fetch_danmu(session, room_id, user_unique_id, referer):
    params = {
        "resp_content_type": "protobuf",
        "did_rule": "3",
        "device_id": "",
        "app_name": "douyin_web",
        "endpoint": "live_pc",
        "support_wrds": "1",
        "user_unique_id": user_unique_id,
        "identity": "audience",
        "need_persist_msg_count": "15",
        "room_id": room_id,
        "version_code": "180800",
        "last_rtt": "0",
        "live_id": "1",
        "aid": "6383",
        "fetch_rule": "1",
        "cursor": "",
        "internal_ext": "",
        "device_platform": "web",
        "cookie_enabled": "true",
        "screen_width": "1463",
        "screen_height": "915",
        "browser_language": "zh-CN",
        "browser_platform": "Win32",
        "browser_name": "Mozilla",
        "browser_version": (
            "5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        ),
        "browser_online": "true",
        "tz_name": "Asia/Shanghai",
    }
    headers = {
        "Accept": "*/*",
        "Referer": referer,
        "User-Agent": USER_AGENT,
    }
    while True:
        try:
            response = session.get(
                "https://live.douyin.com/webcast/im/fetch/",
                params=params,
                headers=headers,
                timeout=40,
            )
        except requests.RequestException as error:
            print(f"[警告] 弹幕请求失败，1 秒后重试: {error}")
            time.sleep(1)
            continue
        response.raise_for_status()
        if not response.content:
            time.sleep(1)
            continue

        content_type = response.headers.get("content-type", "")
        if "protobuf" not in content_type:
            raise RuntimeError(
                f"弹幕接口返回了非 Protobuf 响应: {content_type}; "
                f"body={response.text[:200]!r}"
            )

        try:
            chat_messages, cursor, internal_ext = parse_response(response.content)
        except (ValueError, UnicodeError) as error:
            raise RuntimeError("弹幕 Protobuf 解码失败") from error

        for message in chat_messages:
            print(f"[弹幕] {message['nickname']}: {message['content']}")

        if cursor:
            params["cursor"] = cursor
        if internal_ext:
            params["internal_ext"] = internal_ext
        if not chat_messages:
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="读取抖音直播弹幕")
    parser.add_argument("room_url", nargs="?", default=DEFAULT_ROOM_URL)
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    room_id, user_unique_id = get_room_context(session, args.room_url)
    print(f"room_id={room_id}, user_unique_id={user_unique_id}")
    fetch_danmu(session, room_id, user_unique_id, args.room_url)


if __name__ == "__main__":
    main()
