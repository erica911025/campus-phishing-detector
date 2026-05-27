# 部署到 Streamlit Community Cloud

把本系統部署成一個可分享的公開網址（`https://你的名稱.streamlit.app`），給老師和同學直接試用。全程免費、不需要自己的伺服器。

---

## 你需要準備

1. 一個 **GitHub 帳號**（github.com 免費註冊）。
2. 本專案的全部檔案。
3. （可選）一支 **OpenAI API 金鑰**。沒有也能部署——系統會自動用離線啟發式模式運作，展示完全沒問題；有金鑰才會用 GPT-4o-mini 跑線上判斷。

---

## 重要安全須知（先看這個）

**絕對不要把 API 金鑰上傳到 GitHub。** 本專案的 `.gitignore` 已經設定好會自動忽略 `.env` 與 `.streamlit/secrets.toml`，金鑰請只透過 Streamlit Cloud 後台的 Secrets 設定（見步驟 5）。如果不小心把金鑰推上 GitHub，請立刻到 OpenAI 後台撤銷該金鑰並重新申請。

---

## 步驟一：把專案上傳到 GitHub

**方法 A：用網頁介面（最簡單，不用裝 git）**

1. 登入 github.com，右上角 ＋ →「New repository」。
2. Repository name 填例如 `campus-phishing-detector`，選 **Public**（Community Cloud 公開 app 需要公開 repo；私有 repo 也支援，但公開最單純），先不要勾 README，按「Create repository」。
3. 進到空 repo 頁面，點「uploading an existing file」。
4. 把本專案**所有檔案與資料夾**（含 `data/` 整個資料夾、`.streamlit/` 資料夾、`app.py`、所有 `.py`、`requirements.txt`、`.python-version` 等）拖進去。
   - 注意：`.env`、`.streamlit/secrets.toml` 本來就不該存在或不該上傳；`.env.example` 和 `secrets.toml.example` 可以上傳（它們不含真金鑰）。
5. 下方填個 commit 訊息（如 `initial commit`），按「Commit changes」。

**方法 B：用 git 指令（若你熟悉）**

```bash
cd phishing-detector
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/你的帳號/campus-phishing-detector.git
git push -u origin main
```

> 確認上傳後，repo 裡看得到 `app.py` 和 `data/釣魚信件資料集.xlsx`，但**看不到** `.env` 或真正的 `secrets.toml`。

---

## 步驟二：建立 Streamlit Community Cloud 帳號

1. 前往 **share.streamlit.io**。
2. 用你的 GitHub 帳號登入（Continue with GitHub），依畫面授權。
3. 第一次會要你連結 GitHub 帳號（Connect GitHub account），照提示完成授權，讓 Streamlit 能讀取你的 repo。

---

## 步驟三：部署 App

1. 進入 workspace 後，右上角點 **「Create app」**。
2. 選 **「Deploy a public app from GitHub」**（從 GitHub 部署）。
3. 填三個欄位：
   - **Repository**：選 `你的帳號/campus-phishing-detector`
   - **Branch**：`main`
   - **Main file path**：`app.py`
4. （可選）**Advanced settings** 裡可選 **Python version 3.12**（本專案已附 `.python-version` 指定 3.12，通常會自動帶入）。
5. （可選）**App URL** 欄位可自訂子網域，例如填 `campus-phishing-67`，網址就會是 `https://campus-phishing-67.streamlit.app`。

先別急著按 Deploy，如果你要用線上模式，先做步驟五設定金鑰；只想用離線展示則可直接 Deploy。

---

## 步驟四：等待建置

按下 **Deploy** 後，Community Cloud 會自動讀 `requirements.txt` 安裝套件並啟動，通常幾分鐘內完成。完成後就會出現你的公開網址。

---

## 步驟五：設定 API 金鑰（只有要用線上 GPT 才需要）

1. 在你的 app 頁面右下角（或 workspace 的 app 清單）點 **⋮ → Settings**。
2. 進入 **Secrets** 分頁。
3. 貼上這一行（換成你的真實金鑰）：
   ```toml
   OPENAI_API_KEY = "sk-你的真實金鑰"
   ```
4. 按 **Save**。App 會自動重啟，之後就會以線上 GPT-4o-mini 模式運作。

> 程式碼已寫好：偵測到 secrets 裡有 `OPENAI_API_KEY` 就自動切線上模式，沒有就用離線啟發式。本機開發時則改放在 `.env`，兩邊不衝突。

---

## 步驟六：分享

把網址（如 `https://campus-phishing-67.streamlit.app`）貼進報告、給老師試用即可。之後只要 `git push` 或在 GitHub 改檔，app 會自動更新。

---

## 常見問題

**Q：建置失敗、log 出現套件安裝錯誤？**
多半是 `requirements.txt` 版本問題。本專案已鎖定相容版本範圍，若仍失敗，到 app 的 **Manage app → 看 logs** 找出錯誤套件，調整版本後重新 push。

**Q：app 顯示「離線啟發式」而我已設金鑰？**
確認 Secrets 裡的鍵名正好是 `OPENAI_API_KEY`（大小寫一致），存檔後等 app 重啟。

**Q：資料集讀不到？**
確認 `data/` 整個資料夾（含 `釣魚信件資料集.xlsx`）有一起上傳到 GitHub。程式找不到 xlsx 時會自動改讀 `data/dataset_v2.csv`，所以兩個檔都上傳最保險。

**Q：免費版會不會自動休眠？**
Community Cloud 免費 app 一段時間沒人使用會休眠，下次有人開啟時會自動喚醒（需等幾秒～十幾秒）。Demo 前先自己開一次喚醒即可。
