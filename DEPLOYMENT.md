# Deployment (Streamlit Community Cloud, free)

> Status: **not deployed yet**. A live URL exists only after you finish these steps.

## 1. Code GitHub par push karo (PowerShell)
Project folder me jao, phir:
```powershell
git status
git branch --show-current          # branch ka naam dekho (usually main)
git add .
git status                         # check: .env aur secrets.toml list me NAHI hone chahiye
git commit -m "Finalize Streamlit memory agent"
git push origin main               # agar branch ka naam alag hai to main ki jagah wahi likho
```
Agar folder abhi git repo nahi hai:
```powershell
git init
git branch -M main
git remote add origin https://github.com/siddhanthjain1405-debug/Python-Project-AI.git
git add .
git commit -m "Finalize Streamlit memory agent"
git push -u origin main --force-with-lease
```
(Last wala sirf tab use karo jab tum repo ki purani history overwrite karna chahte ho. Pehle `git pull origin main --allow-unrelated-histories` bhi try kar sakte ho.)

## 2. Streamlit Cloud par app banao
1. https://share.streamlit.io par GitHub se login karo.
2. **Create app** -> repository `siddhanthjain1405-debug/Python-Project-AI`, branch `main`, main file `app.py`.
3. **Advanced settings** -> Python version **3.12**, Secrets me ye likho (apni asli key daalo, kisi ko share mat karo):
```toml
OPENROUTER_API_KEY = "YOUR_KEY"
```
4. **Deploy** dabao. Pehli build me kuch minute lagte hain.

## 3. Check karo
Live URL kholo: sidebar me **AI mode: OpenRouter connected** dikhna chahiye. "hi" bhejo, phir Memory vault me message check karo. Agar Demo mode dikhe to secret ka naam `OPENROUTER_API_KEY` galat hai ya missing hai.

## Notes
- Key kabhi code ya GitHub me nahi jaati: local par `.env`, cloud par Secrets.
- **Memory permanent nahi hai** Streamlit Cloud par: app restart/redeploy par disk reset ho jaati hai. Demo se pehle JSON export kar lo.
- Jiske paas URL hai wo tumhari free-model quota use karega. openrouter.ai/activity me usage dekhte raho.
- Chromadb SQLite error aaye to check karo ki `pysqlite3-binary` install hua (requirements.txt me hai).
