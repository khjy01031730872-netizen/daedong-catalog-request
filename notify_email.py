"""신규 카탈로그 신청 접수 시 담당자(사장) 이메일로 알림을 보낸다.

이 앱은 Streamlit Community Cloud(원격 컨테이너)에서 실행되므로, corp-org의 로컬 전용
공유 카카오 토큰 파일(~/.shared_kakao/kakao_token.json, COM001 PC에만 존재)에는 접근할
수 없다. 카카오 REST API 토큰을 이 앱에 별도로 심으면 refresh_token이 로컬 5개 프로젝트와
또 갈라져 2026-08-27에 실제로 터졌던 KOE322 토큰 회전 충돌이 재발할 위험이 있다.

그래서 이 앱만은 Gmail SMTP(앱 비밀번호, 회전되지 않는 정적 자격증명)로 알림을 보낸다.
kr-stock-screener/corp-org가 이미 쓰는 것과 같은 방식(GMAIL_ADDRESS/GMAIL_APP_PASSWORD)이며,
Streamlit Cloud의 "비밀(Secrets)" 설정에 두 값을 넣어야 동작한다. 값이 없거나 발송이 실패해도
예외를 절대 위로 던지지 않는다 — 신청 자체(DB 저장)는 알림 성공 여부와 무관하게 항상 접수된다.
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _get_secret(name: str) -> str:
    if st is not None:
        try:
            return str(st.secrets.get(name, ""))
        except Exception:
            pass
    import os
    return os.getenv(name, "")


def notify_new_lead(company: str, contact_name: str, email: str, phone: str,
                     interests: str, message: str) -> tuple[bool, str]:
    """신규 신청을 이메일로 통지한다. (성공여부, 실패사유) 반환 — 실패해도 예외를 던지지 않는다.

    leads.db는 Streamlit Cloud 재배포 시 초기화될 수 있으므로(무료 플랜 휘발성 디스크),
    이 이메일 본문에 신청 정보 전체를 담아 사실상의 백업 기록 역할도 겸하게 한다.
    """
    gmail_address = _get_secret("GMAIL_ADDRESS")
    gmail_app_password = _get_secret("GMAIL_APP_PASSWORD")
    if not gmail_address or not gmail_app_password:
        return False, "GMAIL_ADDRESS/GMAIL_APP_PASSWORD 비밀(secret)이 설정되지 않음"

    body = (
        f"카탈로그 신청이 접수됐습니다.\n\n"
        f"회사명: {company}\n"
        f"담당자: {contact_name}\n"
        f"이메일: {email}\n"
        f"연락처: {phone or '(미입력)'}\n"
        f"관심 제품: {interests or '(미선택)'}\n"
        f"문의 내용: {message or '(없음)'}\n"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = gmail_address
    msg["To"] = gmail_address
    msg["Subject"] = f"[대동울타리 카탈로그 신청] {company} — {contact_name}"

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, [gmail_address], msg.as_string())
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
