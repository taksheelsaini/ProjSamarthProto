# Project Samarth — Simple Guide for Students 🎓🚜🌧️

Hello! This README explains the project in easy words. It is written for students and beginners. I use small steps, clear language, and emojis to make it friendly. 😊

This project is a small Streamlit app that helps you compare agriculture (crop production) and climate (rainfall) data. It can also make short data-based policy points (simple arguments) with sources (provenance). 📊🧾

## Table of contents

- What this project does ✅
- What files are here 📁
- How to run the app (step-by-step) ▶️
- Quick demo steps (2 minutes) ⏱️
- Data and where it comes from 📂
- How the outputs work (provenance) 🔎
- What you can change or try next ✨
- Troubleshooting & tips 🛠️

---

## What this project does (short) 🧾

- Lets you load crop production and rainfall data.

- Lets you run four small question templates:

  1. Compare average rainfall and top crops between two states. 🌧️ vs 🌾
  1. Find which district has the highest or lowest production for a crop. 📍
  1. Show a trend for a crop and its correlation with rainfall. 📈
  1. Generate short policy-style arguments to promote one crop over another (data-backed). 🗒️

All outputs show simple provenance: which CSV file or resource the numbers came from, and which years were used. This helps you check the evidence. ✅

---

## What’s in this repository (important files) 📁

- `run_app.py` — the main Streamlit app. Run this to open the web UI. 🌐
- `qa_engine.py` — the code that implements the four question templates. This is where the analysis happens. 🔬
- `generator.py` — simple code that builds short policy arguments from evidence. ✍️
- `normalization.py` / `schema_mapper.py` — helpers that clean and map messy tables into a consistent format. 🧹
- `data/` — sample CSV files used for demos. Use these for reproducible results. 🗂️
- `requirements.txt` — Python dependencies to install. 📦

---

## Simple step-by-step: Run the app locally (macOS / Linux / zsh) 🖥️

1. Open a terminal in this project folder.

1. Create and activate a virtual environment (one-time setup):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install Python packages:

```bash
pip install -r requirements.txt
```

1. Start the Streamlit app:

```bash
streamlit run run_app.py
```

1. The app opens in a browser. If it does not open automatically, go to `http://localhost:8501` in your browser. 🕸️

**Tip:** If you use a different Python command, replace `python3` with your Python executable. ⚠️

---

## Quick demo (2 minutes) — what to click ☝️

1. In the app sidebar, use the Dataset Discovery area. If you have no live API access, click the demo buttons to load the sample CSVs from `data/`. 🗄️

1. Pick the template "Compare rainfall & top crops". Enter two states (for example: `Tamil Nadu` and `Karnataka`) and click Run. You will see average rainfall numbers and the top crops by production. 🌧️➡️🌾

1. Try the district extremes template to see which district has the max or min production for a crop. 📍

1. Try the policy-argument template (promote Crop A vs Crop B). The app will show short arguments and a provenance block listing the data sources used. 🧾✨

---

## Where the data comes from (short) 📦

- The app works with two kinds of data: crop production and rainfall. Sample CSVs live in the `data/` folder so you can always run the app without internet. 🌐❌

- The app can also search CKAN-style data catalogs and attempt to download CSV, Excel or JSON resources if you configure a catalog API key. This is optional. 🔁

**Important:** For reproducible demos we included small normalized CSVs in `data/` so you will get the same results shown in examples. 📂✅

---

## What "provenance" means here (simple) 🔎

- When the app shows a number (for example, average rainfall = 500 mm), it also shows where it got that number: the filename and the years used. This is the provenance. You can open the CSV and see the same rows used in the calculation. 🧾🔗

**Why this helps:** It makes the results checkable. Anyone can look at the CSVs and verify the math. ✅

---

## Good student-level examples (try these) 🧪

- Compare rainfall and top crops: `Tamil Nadu` vs `Karnataka` (years = 2). See rainfall difference and top 3 crops. 🧾
- District extremes: Find the district with highest Rice production in `Tamil Nadu`. 📍
- Trend & correlation: Ask for `Rice` in `Karnataka` for the last 10 years and see if production tracks rainfall. 📈🌧️
- Policy arguments: Promote `Wheat` over `Rice` in a chosen state and read the 3 short data-backed points. 📝

---

## How to read the outputs (simple) 📘

- Each result page has three parts:

  1. Numbers and charts (if any). 📊
  1. Short explanation text. ✍️
  1. Provenance block listing data files, years, and sample rows used as evidence. 🔗

If something looks wrong, open the CSV in `data/` and inspect the rows used by the provenance. ✅

---

## Things you can try to improve the app (projects for learning) 🛠️

- Add more datasets: place new normalized CSVs in `data/` and update the code to recognize them. ➕
- Add row-level links in the provenance block (show exact CSV row numbers). 🔢
- Add unit tests (pytest) for the four templates (`qa_engine.py`). ✅
- Improve the policy-argument wording or scoring in `generator.py`. ✍️

---

## Troubleshooting & common questions ❓

- **Q:** The app shows blank or missing values.

  **A:** Check `data/` CSVs; some values may be missing or non-numeric. Try cleaning the CSV or use the sample CSV that ships with the repo. 🧹

- **Q:** The app does not open at `localhost:8501`.

  **A:** Confirm Streamlit started successfully in the terminal. If not, check for errors there. 🔍

- **Q:** I want to use live data from a catalog.

  **A:** Add catalog credentials to `.env` (if supported) and use the Dataset Discovery tools in the sidebar. This is advanced — start with the local CSVs first. 🌱

---

## Short glossary (easy words) 📚

- **Provenance:** the source of a number (filename, years, sample rows). 🔗
- **Normalized CSV:** a CSV with columns arranged in a standard way so the code can read it easily. 📑
- **CKAN:** a common data-catalog format. You only need it if you want to fetch live data. 🌐

---

## Want to extend this for a school project? 🎓

1. Fork this repo on GitHub.
2. Add a new CSV in `data/` and write a small script to load and test it.
3. Add a simple unit test that checks one QA function returns expected values for your CSV.

---

Thanks for trying Project Samarth! If you want, I can also:

- add a short set of unit tests for the templates, or
- create a one-page lab exercise with step-by-step student tasks.

Have fun learning! 🎉🚜📈



---

## Challenge status — what is done and what remains 🧭

Below is a short, student-friendly summary of the current project state compared to the original challenge goals.

- Done ✅

  - A reproducible Streamlit demo app (`run_app.py`) that loads normalized CSVs from `data/` and answers four template questions with simple provenance. 🌐
  - Four implemented question templates in `qa_engine.py` and a policy-argument builder in `generator.py`. These were smoke-tested locally. 🔬
  - Normalization helpers (`normalization.py`, `schema_mapper.py`) to turn messy tables into the canonical CSV shape used by the app. 🧹
  - Included small normalized CSV examples in `data/` so the app runs without internet. 📂
  - A clean Git history: the repository was reinitialized and pushed with a single commit for a tidy starting point. 🧾
  - Deployment guidance (`DEPLOY_TO_STREAMLIT.md`) and an example secrets file (`.streamlit/secrets.example.toml`) to help publish on Streamlit Community Cloud. 🚀

- Remaining / Future work ⏳

  - Live data ingestion: programmatic discovery and robust fetching from data.gov.in/CKAN catalogs (IMD and agriculture resources). This needs rate-limit handling and retry logic. 🌐🔁
  - Wider schema coverage: more mapping rules to handle diverse real-world table shapes and coded values (units, state/district name variants). 🗺️
  - Station metadata registry: authoritative mapping for weather station → administrative region to improve rainfall aggregation accuracy. 📡➡️📍
  - Row-level provenance: link results back to exact resource URLs and CSV row numbers so each claim is auditable. 🔗🔢
  - Better question parsing: a lightweight NLP router to map free-text questions to the correct template and extract parameters. 🤖🧠
  - Unit tests & CI: add pytest tests for the templates and a GitHub Actions workflow to run the smoke script on every push. ✅
  - Final deliverables: polish conversational UI, make a 2-minute demo video, and prepare the final submission package. 🎬📦

If you want, I can now (pick one):

- implement the live CKAN ingestion plumbing first (longer work), or
- add a small CI workflow and unit tests (quick win), or
- finish by committing this README change and pushing it to the GitHub repo now (I will do this next if you confirm).


