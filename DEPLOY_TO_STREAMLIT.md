Deploying Project Samarth to Streamlit Community Cloud

This short guide shows how to deploy the Streamlit app (`run_app.py`) to Streamlit Community Cloud.

Prerequisites

- A GitHub repository containing this project (already created and pushed).
- A Streamlit account (https://streamlit.io)

Quick deploy (Streamlit Community Cloud)

1. Push your repo to GitHub (already done).
2. Open https://streamlit.io/cloud and sign in with GitHub.
3. Click "New app" → select your GitHub repository `ProjSamarthProto` → choose branch `main` and set the main file to `run_app.py`.
4. Add any secrets in the Secrets UI (see `secrets.example.toml` below for example keys).
5. Click "Deploy". Streamlit will install packages from `requirements.txt` and run the app.

Local notes and troubleshooting

- To run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run run_app.py
```

- If the app fails to start on Streamlit Cloud, open the "Logs" tab in the app dashboard to view the error and adjust.

Secrets example

Create any required secrets in the Streamlit UI. Example keys (place in `.streamlit/secrets.toml` locally for development only):

```toml
# secrets.example.toml
# Example secrets, do NOT commit actual secrets to git
catalog_api_key = "YOUR_API_KEY_IF_ANY"
```

Notes

- The project includes sample data in `data/` so the app works without external APIs.
- If you change `run_app.py`, re-deploy from Streamlit Cloud or push to the `main` branch and Streamlit will redeploy automatically.

That's it — the app should be visible after a short build on Streamlit Cloud.
