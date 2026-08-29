import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header


sender = os.environ["MAIL_USERNAME"]
password = os.environ["MAIL_PASSWORD"]
receiver = os.environ["MAIL_RECEIVER"]

subject = "【测试】北大软微招生通知监控"

body = """这是一封测试邮件。

如果你收到这封邮件，说明：

GitHub Actions
→ QQ邮箱 SMTP
→ 接收邮箱
→ 手机

整个邮件通知链路已经打通。

这只是测试邮件，不代表北大招生网站有新通知。
"""


msg = MIMEText(body, "plain", "utf-8")
msg["Subject"] = Header(subject, "utf-8")
msg["From"] = sender
msg["To"] = receiver


print("正在连接 QQ SMTP...")

with smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30) as server:

    print("正在登录 QQ 邮箱...")

    server.login(sender, password)

    print("正在发送测试邮件...")

    server.sendmail(
        sender,
        receiver,
        msg.as_string()
    )


print("测试邮件发送成功！")