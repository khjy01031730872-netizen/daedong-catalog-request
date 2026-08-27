# 대동울타리 카탈로그 신청 폼 - 상시 서버 실행
# 사내망 어디서든 http://<이 PC의 IP>:8517 로 접속 가능

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

python -m pip install -q streamlit

Write-Host "카탈로그 신청 폼을 사내망에 여는 중 (포트 8517)." -ForegroundColor Cyan
Write-Host "접속 주소: http://<이 PC의 IP>:8517" -ForegroundColor Cyan

python -m streamlit run app.py --server.port 8517 --server.address 0.0.0.0 --server.headless true
