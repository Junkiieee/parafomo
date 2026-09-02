"""E-posta gönderimi. SMTP ayarlıysa gönderir; değilse linki loglar (geliştirme).

SMTP hesabı gelene kadar şifre sıfırlama linki sunucu loguna düşer — akış test
edilebilir, canlıda kullanıcı SMTP verince otomatik e-postaya döner.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from .config import get_settings

logger = logging.getLogger("parafomo.mailer")
_settings = get_settings()


def send_email(to: str, subject: str, body: str) -> bool:
    """E-postayı gönderir. SMTP kapalıysa loglar ve False döner."""
    if not _settings.smtp_enabled:
        logger.warning(
            "SMTP kapalı — e-posta gönderilemedi. Alıcı=%s Konu=%s\n%s",
            to, subject, body,
        )
        return False

    msg = EmailMessage()
    msg["From"] = _settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(_settings.smtp_host, _settings.smtp_port, timeout=20) as server:
            if _settings.smtp_starttls:
                server.starttls()
            if _settings.smtp_user:
                server.login(_settings.smtp_user, _settings.smtp_password)
            server.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError):
        logger.exception("SMTP gönderimi başarısız (alıcı=%s)", to)
        return False


def send_password_reset(to: str, reset_url: str) -> bool:
    subject = "ParaFOMO — Şifre sıfırlama"
    body = (
        "Merhaba,\n\n"
        "ParaFOMO portföy hesabın için şifre sıfırlama talebi aldık. "
        "Aşağıdaki bağlantıya tıklayarak yeni şifreni belirleyebilirsin:\n\n"
        f"{reset_url}\n\n"
        "Bağlantı 1 saat geçerlidir. Bu talebi sen yapmadıysan bu e-postayı "
        "yok sayabilirsin; hesabın güvende.\n\n"
        "ParaFOMO"
    )
    return send_email(to, subject, body)
