import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# 配置
# ============================================================

URL = "https://ss.pku.edu.cn/zsxx/zstz/index.htm"

STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}


# ============================================================
# 获取网页
# ============================================================

def get_page():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    # 北大网站通常是 UTF-8
    response.encoding = response.apparent_encoding

    return response.text


# ============================================================
# 提取招生通知
# ============================================================

def get_notices(html):

    soup = BeautifulSoup(html, "html.parser")

    notices = []

    # 北大招生通知页面通常是：
    #
    # 日期 + 通知标题 + 链接
    #
    # 这里不把网页结构写死得太死，尽可能兼容页面的小改动。

    for a in soup.find_all("a"):

        title = a.get_text(" ", strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        # 只关注带日期的通知
        date_match = re.search(
            r"(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})",
            title
        )

        if not date_match:
            # 有些网页日期不在 a 标签中，因此暂时跳过
            continue

        # 过滤明显无关链接
        if len(title) < 5:
            continue

        full_url = urljoin(URL, href)

        notices.append({
            "title": title,
            "url": full_url,
            "date": (
                f"{date_match.group(1)}-"
                f"{int(date_match.group(2)):02d}-"
                f"{int(date_match.group(3)):02d}"
            )
        })

    # 去重
    unique = {}

    for notice in notices:
        key = (notice["title"], notice["url"])
        unique[key] = notice

    notices = list(unique.values())

    # 保持网页原始顺序
    return notices


# ============================================================
# 状态文件
# ============================================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return []

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


def save_state(notices):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            notices,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# 发送邮件
# ============================================================

def send_email(new_notices):

    sender = os.environ["MAIL_USERNAME"]
    password = os.environ["MAIL_PASSWORD"]
    receiver = os.environ["MAIL_RECEIVER"]

    subject = "【北大软微招生通知】发现新通知"

    body = """
检测到北京大学软件与微电子学院招生通知页面更新。

"""

    for i, notice in enumerate(new_notices, 1):

        body += f"""
{i}. {notice['title']}

发布时间：
{notice['date']}

原文：
{notice['url']}

"""

    body += """
------------------------------
监控页面：
https://ss.pku.edu.cn/zsxx/zstz/index.htm

此邮件由北大软微招生通知自动监控程序发送。
"""

    message = MIMEText(
        body,
        "plain",
        "utf-8"
    )

    message["Subject"] = Header(
        subject,
        "utf-8"
    )

    message["From"] = sender
    message["To"] = receiver

    # QQ邮箱 SMTP
    with smtplib.SMTP_SSL(
        "smtp.qq.com",
        465,
        timeout=30
    ) as server:

        server.login(
            sender,
            password
        )

        server.sendmail(
            sender,
            receiver,
            message.as_string()
        )


# ============================================================
# 主程序
# ============================================================

def main():

    print("=" * 60)
    print("北京大学软件与微电子学院招生通知监控")
    print("=" * 60)

    print("正在访问：")
    print(URL)

    html = get_page()

    notices = get_notices(html)

    if not notices:

        raise RuntimeError(
            "没有解析到任何招生通知，"
            "可能是北大网站页面结构发生变化。"
        )

    print(f"当前发现 {len(notices)} 条通知")

    old_notices = load_state()

    old_keys = {
        (x["title"], x["url"])
        for x in old_notices
    }

    new_notices = [
        x for x in notices
        if (x["title"], x["url"]) not in old_keys
    ]

    # ========================================================
    # 第一次运行
    # ========================================================

    if not old_notices:

        print("第一次运行。")

        # 只记录，不发送邮件
        save_state(notices)

        print("已记录当前通知，不发送提醒。")

        return

    # ========================================================
    # 发现新通知
    # ========================================================

    if new_notices:

        print()
        print("！！！发现新通知！！！")

        for notice in new_notices:

            print(
                notice["date"],
                notice["title"]
            )

        send_email(new_notices)

        print("邮件发送成功。")

    else:

        print("没有发现新通知。")

    # 更新状态
    save_state(notices)


if __name__ == "__main__":
    main()