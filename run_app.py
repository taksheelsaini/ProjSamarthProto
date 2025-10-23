import streamlit as st
from generator import generate_policy_argument
from normalization import normalize_evidence, provenance_score
from qa_engine import (
    compare_avg_rainfall_and_top_crops,
    find_district_extreme,
    trend_and_correlation,
    policy_arguments_for_crop_promotion,
)
import os
import importlib.util
import json


def _get_local_client():
    """Dynamically load app/datagov_client.py as a module and return a DataGovClient instance.

    This uses a file-based import to avoid package name collisions with the top-level `app.py`.
    """
    client_path = os.path.join(os.path.dirname(__file__), 'app', 'datagov_client.py')
    if not os.path.exists(client_path):
        # fallback: try the app/relative path
        client_path = os.path.join(os.getcwd(), 'app', 'datagov_client.py')
    spec = importlib.util.spec_from_file_location('datagov_client', client_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DataGovClient()

st.set_page_config(page_title="Policy Argument & QA Prototype", layout="wide")

st.title("Project Samarth — Policy Argument & Data QA Prototype")

# Project / author info (displayed in-app)
st.markdown("""
**Author:** Taksheel Saini  
**Email:** taksheel13@gmail.com  
**GitHub:** [taksheelsaini](https://github.com/taksheelsaini)
""")

# Free-text question (simple intent router)
st.subheader("Ask a question (free-text)")
free_q = st.text_input("Ask a question about agriculture & climate", value="Compare rainfall in Maharashtra and Karnataka and list top crops")
def intent_router(text: str) -> str:
    t = text.lower()
    if 'compare' in t and 'rain' in t:
        return 'Compare rainfall & top crops (State_X vs State_Y)'
    if 'district' in t and 'highest' in t:
        return 'District extremes for a crop (State_X vs State_Y)'
    if 'trend' in t or 'correl' in t:
        return 'Trend & correlation for crop in region'
    if 'promote' in t or 'promoting' in t:
        return 'Policy arguments to promote crop A over crop B'
    return ''
intent = intent_router(free_q)
if intent:
    st.caption(f"Detected intent: {intent}")

st.sidebar.header("Mode")
mode = st.sidebar.selectbox("Choose mode", ["Policy-argument generator", "Challenge QA templates"])

# Sample questions quick-run
with st.sidebar.expander('Sample questions'):
    st.write('Quick-run the shipped sample QA templates with one click')
    if st.button('Sample 1 — Compare rainfall & top crops (TN vs Karnataka)'):
        st.session_state['sample_run'] = ('compare', {'state_x':'Tamil Nadu','state_y':'Karnataka','years':2,'top_m':3})
    if st.button('Sample 2 — District extremes (Rice: TN vs Karnataka)'):
        st.session_state['sample_run'] = ('extreme', {'state_x':'Tamil Nadu','state_y':'Karnataka','crop':'Rice'})
    if st.button('Sample 3 — Trend & correlation (Rice, Tamil Nadu)'):
        st.session_state['sample_run'] = ('trend', {'region':'Tamil Nadu','crop':'Rice','years':10})
    if st.button('Sample 4 — Policy args (promote Rice vs Wheat in Tamil Nadu)'):
        st.session_state['sample_run'] = ('policy', {'region':'Tamil Nadu','crop_a':'Rice','crop_b':'Wheat','years':5})

# If a sample was requested, run it and display results immediately (regardless of mode)
if st.session_state.get('sample_run'):
    kind, params = st.session_state['sample_run']
    st.subheader('Sample run results')
    if kind == 'compare':
        res = compare_avg_rainfall_and_top_crops(
            params['state_x'], params['state_y'], years=params['years'], top_m=params['top_m'],
            crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'),
            meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})}
        )
        st.write(res)
    elif kind == 'extreme':
        res = find_district_extreme(params['state_x'], params['state_y'], params['crop'], crops_df=st.session_state.get('crop_df'), meta=st.session_state.get('crop_meta'))
        st.write(res)
    elif kind == 'trend':
        res = trend_and_correlation(params['region'], params['crop'], years=params['years'], crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
        st.write(res)
    elif kind == 'policy':
        res = policy_arguments_for_crop_promotion(params['region'], params['crop_a'], params['crop_b'], years=params['years'], crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
        st.write(res)
    # clear the sample flag so it doesn't re-run continuously
    st.session_state['sample_run'] = None

# Session state for selected datasets
if 'crop_df' not in st.session_state:
    st.session_state['crop_df'] = None
    st.session_state['crop_meta'] = None
if 'rain_df' not in st.session_state:
    st.session_state['rain_df'] = None
    st.session_state['rain_meta'] = None

# Dataset discovery UI
with st.sidebar.expander('Dataset discovery & preview'):
    st.write('Search remote catalog (fallback to local samples).')
    crop_q = st.text_input('Crop dataset keyword', value='crop production')
    if st.button('Load crop dataset (local)'):
        with st.spinner('Loading local crop dataset...'):
            client = _get_local_client()
            df, meta = client.get_agriculture_dataframe()
            st.session_state['crop_df'] = df
            st.session_state['crop_meta'] = meta
            st.success('Local crop dataset loaded (preview below).')

    rain_q = st.text_input('Rainfall dataset keyword', value='rainfall IMD')
    if st.button('Load rainfall dataset (local)'):
        with st.spinner('Loading local rainfall dataset...'):
            client = _get_local_client()
            df, meta = client.get_rainfall_dataframe()
            st.session_state['rain_df'] = df
            st.session_state['rain_meta'] = meta
            st.success('Local rainfall dataset loaded (preview below).')

    if st.session_state.get('crop_df') is not None:
        st.markdown('**Crop dataset preview**')
        st.dataframe(st.session_state['crop_df'].head(10))
    if st.session_state.get('rain_df') is not None:
        st.markdown('**Rainfall dataset preview**')
        st.dataframe(st.session_state['rain_df'].head(10))

if mode == "Policy-argument generator":
    st.header("Policy Argument Generator")
    question = st.text_area("Policy question", value="Should we expand subsidized irrigation programs in region X?", height=120)
    top_k = st.slider("Number of arguments", 1, 6, 3)
    if st.button("Generate arguments"):
        # load sample evidence (fall back if file missing)
        try:
            with open("data/sample_evidence.json","r") as f:
                evidence = json.load(f)
        except FileNotFoundError:
            evidence = [
                {"id": "local-1", "title": "Local irrigation study", "text": "Irrigation coverage increased yields by 12% in pilot regions.", "source": "local://sample"},
            ]

        norm = normalize_evidence(evidence)
        args = generate_policy_argument(question, norm, top_k=top_k)

        st.subheader("Generated Arguments")
        for i,a in enumerate(args, start=1):
            st.markdown(f"**{i}. {a['title']}**")
            st.write(a['argument'])
            st.caption(f"Provenance score: {a.get('provenance', 0):.2f} — Sources: {', '.join(a.get('sources',[]))}")

        st.subheader("Provenance Summary")
        st.write({"aggregate_provenance": provenance_score(args)})

else:
    st.header("Challenge QA templates")
    st.markdown("Use the small demo templates that query local sample datasets (crop production and rainfall).")
    q = st.selectbox("Select question", [
        "Compare rainfall & top crops (State_X vs State_Y)",
        "District extremes for a crop (State_X vs State_Y)",
        "Trend & correlation for crop in region",
        "Policy arguments to promote crop A over crop B",
    ])

    # If a sample button was clicked, run it and display results here
    if st.session_state.get('sample_run') and st.session_state['sample_run'][0] == 'compare':
        _, params = st.session_state['sample_run']
        res = compare_avg_rainfall_and_top_crops(
            params['state_x'], params['state_y'], years=params['years'], top_m=params['top_m'],
            crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'),
            meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})}
        )
        st.subheader("Sample 1 Results")
        st.write(res)
        # clear sample_run after display
        st.session_state['sample_run'] = None

    if q == "Compare rainfall & top crops (State_X vs State_Y)":
        col1, col2 = st.columns(2)
        with col1:
            state_x = st.text_input("State X", value="State_X")
            years = st.number_input("Last N years", value=3, min_value=1, max_value=10)
        with col2:
            state_y = st.text_input("State Y", value="State_Y")
            top_m = st.number_input("Top M crops", value=3, min_value=1, max_value=10)

        if st.button("Run QA"):
            res = compare_avg_rainfall_and_top_crops(
                state_x,
                state_y,
                years=years,
                top_m=top_m,
                crops_df=st.session_state.get('crop_df'),
                rain_df=st.session_state.get('rain_df'),
                meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})}
            )
            st.subheader("Results")
            st.write("Average annual rainfall (last {} years):".format(years))
            st.write(res.get('rainfall'))
            st.write("Top crops by production:")
            st.write(res.get('top_crops'))
            st.subheader("Provenance")
            st.write(res.get('provenance'))

    elif st.session_state.get('sample_run') and st.session_state['sample_run'][0] == 'extreme':
        _, params = st.session_state['sample_run']
        res = find_district_extreme(params['state_x'], params['state_y'], params['crop'], crops_df=st.session_state.get('crop_df'), meta=st.session_state.get('crop_meta'))
        st.subheader('Sample 2 Results')
        st.write(res)
        st.session_state['sample_run'] = None

    elif q == "District extremes for a crop (State_X vs State_Y)":
        col1, col2 = st.columns(2)
        with col1:
            state_x = st.text_input("State X", value="State_X")
            crop = st.text_input("Crop", value="Wheat")
        with col2:
            state_y = st.text_input("State Y", value="State_Y")

        if st.button("Run QA - extremes"):
            res = find_district_extreme(state_x, state_y, crop, crops_df=st.session_state.get('crop_df'), meta=st.session_state.get('crop_meta'))
            st.write(res)

    elif st.session_state.get('sample_run') and st.session_state['sample_run'][0] == 'trend':
        _, params = st.session_state['sample_run']
        res = trend_and_correlation(params['region'], params['crop'], years=params['years'], crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
        st.subheader('Sample 3 Results')
        st.write(res)
        st.session_state['sample_run'] = None

    elif q == "Trend & correlation for crop in region":
        region = st.text_input("Region/State", value="State_X")
        crop = st.text_input("Crop", value="Wheat")
        years = st.number_input("Years to analyze", value=10, min_value=1, max_value=50)
        if st.button("Run Trend"):
            res = trend_and_correlation(region, crop, years=years, crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
            st.write(res)

    elif st.session_state.get('sample_run') and st.session_state['sample_run'][0] == 'policy':
        _, params = st.session_state['sample_run']
        res = policy_arguments_for_crop_promotion(params['region'], params['crop_a'], params['crop_b'], years=params['years'], crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
        st.subheader('Sample 4 Results')
        st.write(res)
        st.session_state['sample_run'] = None

    else:  # policy arguments
        region = st.text_input("Region/State", value="State_X")
        crop_a = st.text_input("Crop A (promote)", value="Wheat")
        crop_b = st.text_input("Crop B (replace)", value="Rice")
        years = st.number_input("Years to use", value=5, min_value=1, max_value=20)
        if st.button("Generate policy arguments"):
            res = policy_arguments_for_crop_promotion(region, crop_a, crop_b, years=years, crops_df=st.session_state.get('crop_df'), rain_df=st.session_state.get('rain_df'), meta={**(st.session_state.get('crop_meta') or {}), **(st.session_state.get('rain_meta') or {})})
            st.write(res)
