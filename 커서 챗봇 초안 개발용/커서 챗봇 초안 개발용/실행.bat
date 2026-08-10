@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  생물교육과 챗봇을 실행합니다...
echo  브라우저가 자동으로 열립니다.
echo  종료하려면 이 창에서 Ctrl+C 를 누르세요.
echo ========================================
echo.
python -m streamlit run app.py
pause
