import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

from datagov_client import DataGovClient
from normalize import normalize_agriculture, normalize_rainfall, join_agri_climate
from policy import generate_policy_arguments, provenance_score

load_dotenv()

st.set_page_config(layout="wide", page_title="Project Samarth - Q&A")

st.title("Project Samarth — Agriculture ⚖️ Climate Q&A (Prototype)")

# Sidebar
st.sidebar.header("Configuration")
st.sidebar.write("Using local normalized CSVs (no live API fetch)")

client = DataGovClient()

with st.spinner("Loading data..."):
    agri_df, agri_meta = client.get_agriculture_dataframe()
    rain_df, rain_meta = client.get_rainfall_dataframe()

agri_norm = normalize_agriculture(agri_df)
rain_norm = normalize_rainfall(rain_df)

st.subheader("Ask a question about crops and rainfall")
question = st.text_input("Type a natural-language question (see samples in README)", value="Compare average annual rainfall in Maharashtra vs Karnataka for the last 5 years, and list top 3 cereals by production in each.")

col1, col2 = st.columns([4,1])
with col2:
    if st.button("Run"):
        st.session_state['last_question'] = question

if 'last_question' not in st.session_state:
    st.session_state['last_question'] = question

user_q = st.session_state['last_question']

def parse_question(q):
    q_low = q.lower()
    parsed = {'type': 'unknown'}
    if 'compare' in q_low and 'rainfall' in q_low and 'top' in q_low:
        parsed['type'] = 'compare_rainfall_and_top_crops'
    elif 'highest' in q_low and 'production' in q_low:
        parsed['type'] = 'district_max_production'
    elif 'trend' in q_low or 'correl' in q_low:
        parsed['type'] = 'trend_and_correlation'
    elif 'promote' in q_low or 'policy' in q_low:
        parsed['type'] = 'policy_support'
    return parsed

parsed = parse_question(user_q)
st.markdown(f"**Detected question type:** `{parsed['type']}`")

def executor_compare(agri, rain, top_m=3, years=5, state_x="Maharashtra", state_y="Karnataka"):
    yrs = sorted(rain['year'].dropna().unique())
    if len(yrs) == 0:
        return {"error": "No rainfall years available"}, []
    recent_years = yrs[-years:]
    rain_sub = rain[rain['year'].isin(recent_years)]
    agg_rain = rain_sub.groupby('state').rainfall_mm.mean().reset_index().rename(columns={'rainfall_mm':'avg_annual_rainfall_mm'})

    agri_sub = agri[agri['year'].isin(recent_years)]
    top_crops = agri_sub.groupby(['state','crop']).production_tonnes.sum().reset_index()
    topX = top_crops.groupby('state').apply(lambda d: d.sort_values('production_tonnes', ascending=False).head(top_m)).reset_index(drop=True)
    return {'rain': agg_rain, 'top_crops': topX, 'years': recent_years}, [agri_meta, rain_meta]

def executor_district_max(agri, crop, state):
    last_year = int(agri['year'].dropna().max())
    sub = agri[(agri['state']==state) & (agri['crop'].str.contains(crop, case=False)) & (agri['year']==last_year)]
    if len(sub)==0:
        return {"error": f"No rows for {crop} in {state} for year {last_year}"}, [agri_meta]
    max_row = sub.sort_values('production_tonnes', ascending=False).iloc[0]
    min_row = sub.sort_values('production_tonnes', ascending=True).iloc[0]
    return {"max": max_row.to_dict(), "min": min_row.to_dict(), "year": int(last_year)}, [agri_meta]

def executor_trend_and_corr(agri, rain, crop, region_state=None):
    # 10-year window or available
    yrs = sorted(agri['year'].dropna().unique())
    if len(yrs) == 0:
        return {"error":"No years in agriculture data"}, [agri_meta, rain_meta]
    window = yrs[-10:]
    a = agri[agri['year'].isin(window) & agri['crop'].str.contains(crop, case=False)]
    if region_state:
        a = a[a['state']==region_state]
        r = rain[rain['state']==region_state]
    else:
        r = rain
    a_ts = a.groupby('year').production_tonnes.sum().reset_index()
    r_ts = r[r['year'].isin(window)].groupby('year').rainfall_mm.mean().reset_index()
    # align years
    df = a_ts.merge(r_ts, on='year', how='inner')
    if df.empty:
        return {"error":"No overlapping years for trend/correlation"}, [agri_meta, rain_meta]
    # correlation
    from scipy.stats import pearsonr
    corr = None
    try:
        corr, p = pearsonr(df['production_tonnes'], df['rainfall_mm'])
    except Exception:
        corr = None
    return {"trend": df, "corr": corr}, [agri_meta, rain_meta]

# simple policy argument generator wrapper
def executor_policy_support(agri, rain, crop_a, crop_b, region_state=None, years=5):
    # uses the included policy module
    args = generate_policy_arguments(agri, rain, crop_a, crop_b, region_state=region_state, years=years)
    score = provenance_score(args)
    return {"arguments": args, "provenance_score": score}, [agri_meta, rain_meta]

result = None
provenance = []
if parsed['type'] == 'compare_rainfall_and_top_crops':
    top_m = 3
    years = 5
    result, provenance = executor_compare(agri_norm, rain_norm, top_m=top_m, years=years)
elif parsed['type'] == 'district_max_production':
    ql = user_q.lower()
    crop = "sugarcane" if "sugarcane" in ql else "rice"
    state = "Maharashtra" if "maharashtra" in ql else "Karnataka"
    result, provenance = executor_district_max(agri_norm, crop, state)
elif parsed['type'] == 'trend_and_correlation':
    ql = user_q.lower()
    crop = "rice" if "rice" in ql else "rice"
    state = None
    result, provenance = executor_trend_and_corr(agri_norm, rain_norm, crop, region_state=state)
elif parsed['type'] == 'policy_support':
    # naive extraction
    ql = user_q.lower()
    crop_a = "millet" if "millet" in ql else "sorghum"
    crop_b = "rice" if "rice" in ql else "paddy"
    state = None
    result, provenance = executor_policy_support(agri_norm, rain_norm, crop_a, crop_b, region_state=state)
else:
    result = {"error": "Question type not supported by this minimal prototype yet."}

st.subheader("Answer")
if isinstance(result, dict) and 'error' in result:
    st.error(result['error'])
else:
    if parsed['type'] == 'compare_rainfall_and_top_crops':
        st.markdown("### Average annual rainfall (recent years)")
        st.dataframe(result['rain'].sort_values('avg_annual_rainfall_mm', ascending=False))
        st.markdown("### Top crops by production (sum across selected years)")
        st.dataframe(result['top_crops'].sort_values(['state','production_tonnes'], ascending=[True,False]))
        fig = px.bar(result['rain'], x='state', y='avg_annual_rainfall_mm', title="Avg annual rainfall (mm)")
        st.plotly_chart(fig, use_container_width=True)
    elif parsed['type'] == 'district_max_production':
        st.markdown(f"District with max production in {result['max']['state']} ({result['year']})")
        st.json(result)
    elif parsed['type'] == 'trend_and_correlation':
        st.markdown("### Trend and correlation")
        st.dataframe(result['trend'])
        st.markdown(f"Pearson correlation (production vs rainfall): {result['corr']}")
        fig = px.line(result['trend'], x='year', y=['production_tonnes','rainfall_mm'], title='Production vs Rainfall (aligned years)')
        st.plotly_chart(fig, use_container_width=True)
    elif parsed['type'] == 'policy_support':
        st.markdown("### Policy support: data-backed arguments")
        for i, arg in enumerate(result['arguments']):
            st.markdown(f"**{i+1}.** {arg['text']}")
            st.write("Sources:")
            for s in arg['sources']:
                st.markdown(f"- {s.get('title','dataset')} ({s.get('url')})")
        st.markdown(f"Provenance score: {result['provenance_score']}")
    else:
        st.write(result)

st.sidebar.header("Sources & Methods")
for meta in provenance:
    if not meta:
        continue
    st.sidebar.markdown(f"**{meta.get('title','Unknown dataset')}**")
    if meta.get('publisher'):
        st.sidebar.write(meta.get('publisher'))
    if meta.get('url'):
        st.sidebar.markdown(f"[Resource link]({meta.get('url')})")
st.sidebar.markdown("Methods: averages, sums, ranks, Pearson correlation computed over normalized fields `production_tonnes` and `rainfall_mm`")

st.markdown("---")
st.markdown("Sample questions:")
st.write("- Compare average annual rainfall in Maharashtra vs Karnataka for the last 5 years, and list top 3 cereals by production in each.")
st.write("- Which district in Maharashtra had the highest sugarcane production last year?")
