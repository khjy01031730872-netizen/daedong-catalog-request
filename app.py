"""
대동울타리 카탈로그 신청 폼 — 웹사이트 방문자가 스스로 이메일을 남기면(옵트인 동의),
그 순간부터 합법적으로 카탈로그·안내 자료를 보낼 수 있다.

법적 근거: 정보통신망법 제50조는 영리목적 광고성 정보 전송에 수신자의 사전 동의를
요구한다. 이 폼은 방문자가 직접 정보를 남기고 수집·이용에 명시 동의하는 구조라
발신 근거가 확보된다(2026-08-27, "인스타·메타 스크래핑으로 이메일 모아 자동발송"
요청을 대신해 채택한 합법적 대안 — 자세한 배경은 CLAUDE.md 참고).

동의 없이 소셜미디어에서 연락처를 긁어와 대량 발송하는 방식은 절대 만들지 않는다.
"""
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "leads.db"
CATALOG_PATH = BASE_DIR / "대동울타리_제품카탈로그.pptx"

CORP_ORG_DIR = BASE_DIR.parent / "corp-org"
if str(CORP_ORG_DIR) not in sys.path:
    sys.path.insert(0, str(CORP_ORG_DIR))

st.set_page_config(page_title="대동울타리 — 제품 카탈로그 신청", page_icon="🛡️", layout="centered")

INTEREST_OPTIONS = ["메쉬휀스", "디자인휀스", "안전난간", "주물휀스", "합성목재 가림판", "특수 제작(맞춤)", "기타"]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            company TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            interests TEXT,
            message TEXT,
            consented INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_lead(company, contact_name, email, phone, interests, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO leads (created_at, company, contact_name, email, phone, interests, message, consented) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), company, contact_name, email, phone,
         ", ".join(interests), message),
    )
    conn.commit()
    conn.close()


def notify_new_lead(company, contact_name, email):
    """새 신청이 들어오면 카카오톡으로 담당자에게 알린다. 실패해도 신청 자체는 막지 않는다
    (알림 실패로 잠재고객 신청이 유실되면 안 된다)."""
    try:
        from notify.kakao import send_memo
        send_memo(f"📩 카탈로그 신청 접수\n업체: {company}\n담당자: {contact_name}\n이메일: {email}")
    except Exception as e:
        st.session_state["_notify_error"] = str(e)


def valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


init_db()

st.title("🛡️ 대동울타리 제품 카탈로그 신청")
st.caption("휀스·난간·주물휀스 전문 제조·시공 — 경기 화성시 마도면")

st.markdown(
    "아래 정보를 남겨 주시면 **제품 카탈로그를 바로 내려받으실 수 있고**, "
    "담당자가 이메일로 상세 견적·안내자료를 보내드립니다."
)

with st.form("catalog_request", clear_on_submit=False):
    col1, col2 = st.columns(2)
    company = col1.text_input("회사명 *")
    contact_name = col2.text_input("담당자명 *")
    email = col1.text_input("이메일 *", placeholder="example@company.com")
    phone = col2.text_input("연락처 (선택)", placeholder="010-0000-0000")
    interests = st.multiselect("관심 제품 (선택)", INTEREST_OPTIONS)
    message = st.text_area("문의 내용 (선택)", placeholder="현장 위치, 필요 규격 등 자유롭게 적어주세요.")

    with st.expander("개인정보 수집·이용 안내 (필수 동의 항목 포함)", expanded=True):
        st.markdown(
            "- **수집 항목:** 회사명, 담당자명, 이메일, 연락처(입력 시), 문의 내용\n"
            "- **수집 목적:** 카탈로그·견적 자료 발송, 문의 응대\n"
            "- **보유 기간:** 신청일로부터 1년 또는 동의 철회 시까지\n"
            "- 동의를 거부할 권리가 있으며, 거부 시 카탈로그 자동 발송·신청이 제한됩니다.\n"
            "- 수신을 원치 않으시면 받으신 이메일에서 언제든 수신거부하실 수 있습니다."
        )
        consent = st.checkbox("위 개인정보 수집·이용에 동의합니다. *")

    submitted = st.form_submit_button("카탈로그 신청하기", type="primary", use_container_width=True)

if submitted:
    errors = []
    if not company.strip():
        errors.append("회사명을 입력해 주세요.")
    if not contact_name.strip():
        errors.append("담당자명을 입력해 주세요.")
    if not valid_email(email.strip()):
        errors.append("올바른 이메일 주소를 입력해 주세요.")
    if not consent:
        errors.append("개인정보 수집·이용에 동의해 주셔야 신청이 가능합니다.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        save_lead(company.strip(), contact_name.strip(), email.strip(), phone.strip(), interests, message.strip())
        notify_new_lead(company.strip(), contact_name.strip(), email.strip())
        st.success("신청이 접수됐습니다! 아래에서 카탈로그를 바로 받아보세요. 담당자가 곧 이메일로 연락드리겠습니다.")
        if CATALOG_PATH.exists():
            st.download_button(
                "⬇️ 카탈로그 바로 받기",
                data=CATALOG_PATH.read_bytes(),
                file_name=CATALOG_PATH.name,
                use_container_width=True,
            )
        if st.session_state.get("_notify_error"):
            st.caption(f"(내부 알림 전송은 실패했지만 신청 정보는 정상 저장됐습니다: {st.session_state['_notify_error']})")
