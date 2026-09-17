# התקנה ב-Windows (Custom Fork)

## הדרך הקלה

1. Node.js **22** (לא 24): https://nodejs.org/en/download
2. Python **3.11 או 3.12**: https://www.python.org/downloads/
3. בתיקיית `open-webui` לחץ פעמיים על **INSTALL_WINDOWS.bat**

המתקין שואל YES/NO:
- npm — הורדת Frontend
- pip כבד (~1–3GB) — YES אוטומטי, או NO ואז הורדה ידנית + Enter להמשך
- הפעלה על פורט 8080

## רק להפעיל

`START_WINDOWS.bat` → http://localhost:8080

## Node 24

לא נתמך. התקן Node 22 והרץ שוב.

## pip כבד / נכשל

בחר NO במתקין, הורד מ-https://pytorch.org/get-started/locally/ ואז:
```
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```
לחץ Enter במתקין או הרץ START_WINDOWS.bat
