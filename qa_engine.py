"""QA utilities that operate on local normalized CSVs and return simple provenance.

This module is intentionally minimal: it always uses the normalized CSVs placed in
the repository under data/ and returns provenance URIs pointing at those files.
"""
from typing import Dict, Any, List
import os
import pandas as pd
import numpy as np

HERE = os.path.dirname(__file__)
# Data files live in the `data/` folder under the project root (same directory as this file)
PROD_CSV = os.path.join(HERE, "data", "normalized_production_2018_19.csv")
RAIN_CSV = os.path.join(HERE, "data", "normalized_rainfall_2018_19.csv")


def _read_csv(path: str) -> pd.DataFrame:
    try:
        # Use the python engine and skip malformed lines to be tolerant of messy CSVs.
        return pd.read_csv(path, engine='python', on_bad_lines='skip')
    except Exception:
        return pd.DataFrame()


def _load_crops_df() -> pd.DataFrame:
    df = _read_csv(PROD_CSV)
    if df.empty:
        return pd.DataFrame([{"state": "State_X", "district": "D1", "crop": "Wheat", "year": 2020, "production": 1000}])
    # Normalize column names and types to canonical expectations
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    # Map alternative production column names to `production`
    if 'production_tonnes' in df.columns and 'production' not in df.columns:
        df['production'] = pd.to_numeric(df['production_tonnes'], errors='coerce')
    elif 'production' in df.columns:
        df['production'] = pd.to_numeric(df['production'], errors='coerce')
    # Ensure year is numeric
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    # Normalize state strings
    if 'state' in df.columns:
        df['state'] = df['state'].astype(str).str.strip().str.title()
    return df


def _load_rain_df() -> pd.DataFrame:
    df = _read_csv(RAIN_CSV)
    if df.empty:
        return pd.DataFrame([{"state": "State_X", "year": 2020, "avg_annual_rainfall": 800}])
    # If CSV is in wide per-station layout (columns like 'actual_rainfall_in_<station>_in_mm'),
    # melt to long and aggregate to annual per state-year.
    df_orig = df.copy()
    cols = list(df_orig.columns)
    lc = [c.strip().lower() for c in cols]
    station_cols = [cols[i] for i, c in enumerate(lc) if ('actual' in c and 'rain' in c) or c.startswith('actual_rainfall')]
    if station_cols:
        id_vars = [c for c in cols if c not in station_cols]
        long = df_orig.melt(id_vars=id_vars, value_vars=station_cols, var_name='station', value_name='rain_mm')
        # Clean station names
        long['station'] = long['station'].astype(str).str.replace('actual_rainfall_in_','', case=False)
        long['station'] = long['station'].str.replace('_in_mm','', case=False)
        long['station'] = long['station'].str.replace('_',' ').str.strip()
        # Try to extract year from common id_vars (month/peroid/period)
        year_vals = None
        for cand in ['month','peroid','period','mon']:
            for oc in id_vars:
                if oc.strip().lower() == cand:
                    year_vals = long[oc].astype(str).str.extract(r"(\d{4})", expand=False)
                    break
            if year_vals is not None:
                break
        if year_vals is None:
            # try any id_var column for 4-digit year
            for oc in id_vars:
                yrs = long[oc].astype(str).str.extract(r"(\d{4})", expand=False)
                if yrs.notna().any():
                    year_vals = yrs
                    break
        if year_vals is None:
            long['year'] = pd.NA
        else:
            long['year'] = pd.to_numeric(year_vals, errors='coerce')
        # Station->state mapping: try a small CSV mapping first, else fall back to heuristics
        mapping_path = os.path.join(HERE, 'data', 'station_to_state.csv')
        station_map = {}
        try:
            sm = pd.read_csv(mapping_path, engine='python', on_bad_lines='skip')
            for _, r in sm.iterrows():
                k = str(r.get('station_substring','')).strip().lower()
                v = str(r.get('state','')).strip()
                if k:
                    station_map[k] = v
        except Exception:
            station_map = {}

        def station_to_state(s: str) -> str:
            s_low = (s or '').lower()
            # check mapping by substring
            for sub, st in station_map.items():
                if sub and sub in s_low:
                    return st
            # fallback heuristic (Tamil Nadu heavy sample)
            tn_subs = ['karur','aravakurichi','paramathi','anaipalyam','kulithalai','thogaimalai','kadavur','palaviduthi','mayanur','panchapatti']
            for sub in tn_subs:
                if sub in s_low:
                    return 'Tamil Nadu'
            return 'Unknown'
        long['state'] = long['station'].apply(station_to_state)
        long['rain_mm'] = pd.to_numeric(long['rain_mm'], errors='coerce')
        agg = long.groupby(['state','year'])['rain_mm'].mean().reset_index().rename(columns={'rain_mm':'avg_annual_rainfall'})
        # Normalize state strings
        if 'state' in agg.columns:
            agg['state'] = agg['state'].astype(str).str.strip().str.title()
        return agg
    # Non-wide layouts: normalize column names and pick the rainfall-like column
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    if 'rainfall_mm' in df.columns and 'avg_annual_rainfall' not in df.columns:
        df['avg_annual_rainfall'] = pd.to_numeric(df['rainfall_mm'], errors='coerce')
    elif 'avg_annual_rainfall' in df.columns:
        df['avg_annual_rainfall'] = pd.to_numeric(df['avg_annual_rainfall'], errors='coerce')
    else:
        for c in df.columns:
            if 'rain' in c and c not in ('state','district'):
                df['avg_annual_rainfall'] = pd.to_numeric(df[c], errors='coerce')
                break
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    if 'state' in df.columns:
        df['state'] = df['state'].astype(str).str.strip().str.title()
    return df


def compare_avg_rainfall_and_top_crops(state_x: str, state_y: str, years: int = 3, top_m: int = 3, crops_df: pd.DataFrame = None, rain_df: pd.DataFrame = None, meta: Dict[str, Any] = None, **_kwargs) -> Dict[str, Any]:
    # Allow caller to provide pre-loaded dataframes (from Streamlit session state)
    crops = crops_df if crops_df is not None else _load_crops_df()
    rain = rain_df if rain_df is not None else _load_rain_df()

    # coerce year to numeric
    if 'year' in crops.columns:
        crops['year'] = pd.to_numeric(crops['year'], errors='coerce')
    if 'year' in rain.columns:
        rain['year'] = pd.to_numeric(rain['year'], errors='coerce')

    available_years = sorted(rain['year'].dropna().unique(), reverse=True)
    years_to_use = available_years[:years]

    def avg_rain(state):
        sel = rain[(rain['state'] == state) & (rain['year'].isin(years_to_use))]
        return float(sel['avg_annual_rainfall'].mean()) if not sel.empty else None

    rain_x = avg_rain(state_x)
    rain_y = avg_rain(state_y)

    csel_x = crops[(crops['state'] == state_x) & (crops['year'].isin(years_to_use))]
    top_x = csel_x.groupby('crop')['production'].sum().sort_values(ascending=False).head(top_m)

    csel_y = crops[(crops['state'] == state_y) & (crops['year'].isin(years_to_use))]
    top_y = csel_y.groupby('crop')['production'].sum().sort_values(ascending=False).head(top_m)

    return {
        'rainfall': {state_x: rain_x, state_y: rain_y},
        'top_crops': {state_x: top_x.to_dict(), state_y: top_y.to_dict()},
        'provenance': {
            'rainfall_source': f'local://data/{os.path.basename(RAIN_CSV)}',
            'crops_source': f'local://data/{os.path.basename(PROD_CSV)}',
            'years_used': years_to_use,
        },
    }


def find_district_extreme(state_x: str, state_y: str, crop: str, crops_df: pd.DataFrame = None, meta: Dict[str, Any] = None, **_kwargs) -> Dict[str, Any]:
    crops = crops_df if crops_df is not None else _load_crops_df()
    recent_year = int(crops['year'].dropna().max())
    sel_x = crops[(crops['state'] == state_x) & (crops['crop'] == crop) & (crops['year'] == recent_year)]
    sel_y = crops[(crops['state'] == state_y) & (crops['crop'] == crop) & (crops['year'] == recent_year)]

    def extreme(sel, kind='max'):
        if sel.empty:
            return None
        if kind == 'max':
            row = sel.loc[sel['production'].idxmax()]
        else:
            row = sel.loc[sel['production'].idxmin()]
        return {'district': row['district'], 'production': float(row['production']), 'year': int(row['year'])}

    return {
        'state_x_max': extreme(sel_x, 'max'),
        'state_y_min': extreme(sel_y, 'min'),
        'provenance': {'crops_source': f'local://data/{os.path.basename(PROD_CSV)}', 'year': recent_year},
    }


def trend_and_correlation(region: str, crop: str, years: int = 10, crops_df: pd.DataFrame = None, rain_df: pd.DataFrame = None, meta: Dict[str, Any] = None, **_kwargs) -> Dict[str, Any]:
    crops = crops_df if crops_df is not None else _load_crops_df()
    rain = rain_df if rain_df is not None else _load_rain_df()
    c = crops[(crops['state'] == region) & (crops['crop'] == crop)]
    if c.empty:
        return {'error': 'No crop data for region'}

    yearly = c.groupby('year')['production'].sum().sort_index()
    r = rain[rain['state'] == region].set_index('year')['avg_annual_rainfall']
    df = pd.DataFrame({'production': yearly}).join(r, how='left').dropna()
    if df.empty:
        return {'error': 'No overlapping rainfall data for region'}

    corr = float(df['production'].corr(df['avg_annual_rainfall']))
    trend = np.polyfit(df.index.astype(float), df['production'].values.astype(float), 1)
    slope = float(trend[0])
    return {
        'trend_slope': slope,
        'correlation': corr,
        'years': df.index.tolist(),
        'data': df.reset_index().to_dict(orient='records'),
        'provenance': {'crops': f'local://data/{os.path.basename(PROD_CSV)}', 'rain': f'local://data/{os.path.basename(RAIN_CSV)}'},
    }


def policy_arguments_for_crop_promotion(region: str, crop_a: str, crop_b: str, years: int = 5, crops_df: pd.DataFrame = None, rain_df: pd.DataFrame = None, meta: Dict[str, Any] = None, **_kwargs) -> Dict[str, Any]:
    crops = crops_df if crops_df is not None else _load_crops_df()
    rain = rain_df if rain_df is not None else _load_rain_df()
    yrs = sorted(crops['year'].dropna().unique(), reverse=True)[:years]
    cA = crops[(crops['state'] == region) & (crops['crop'] == crop_a) & (crops['year'].isin(yrs))]
    cB = crops[(crops['state'] == region) & (crops['crop'] == crop_b) & (crops['year'].isin(yrs))]

    args: List[Dict[str, Any]] = []
    prov = {'crops': f'local://data/{os.path.basename(PROD_CSV)}', 'rain': f'local://data/{os.path.basename(RAIN_CSV)}', 'years_used': yrs}

    # Compute candidate metrics even when one of the crop series is small
    def safe_slope(df):
        if len(df) < 2:
            return 0.0
        return float(np.polyfit(sorted(df['year'].astype(float)), df.sort_values('year')['production'].astype(float), 1)[0])

    slopeA = safe_slope(cA)
    slopeB = safe_slope(cB)

    def corr_with_rain(df):
        prod = df.groupby('year')['production'].sum().rename('production').to_frame()
        rain_series = rain[rain['state'] == region].set_index('year')['avg_annual_rainfall']
        dfj = prod.join(rain_series, how='left').dropna()
        if len(dfj) < 2:
            return 0.0, 0
        return float(dfj['production'].corr(dfj['avg_annual_rainfall'])), len(dfj)

    corrA, nA = corr_with_rain(cA)
    corrB, nB = corr_with_rain(cB)

    varA = float(cA['production'].var()) if len(cA) > 1 else float('inf')
    varB = float(cB['production'].var()) if len(cB) > 1 else float('inf')

    # Build scored candidate arguments
    candidates = []
    # 1. Trend advantage
    candidates.append((abs(slopeA - slopeB), {'title': 'Production trend comparison', 'argument': f"{crop_a} slope {slopeA:.2f} vs {crop_b} slope {slopeB:.2f} over last {years} yrs.", 'confidence': 0.5}))
    # 2. Rainfall dependence (lower corr is better resilience)
    candidates.append((abs(corrA - corrB), {'title': 'Rainfall-dependence difference', 'argument': f"Correlation with rainfall: {crop_a}={corrA:.2f} (n={nA}), {crop_b}={corrB:.2f} (n={nB}). Lower correlation suggests less dependence on rainfall.", 'confidence': 0.5}))
    # 3. Variability advantage (lower variance is better)
    candidates.append((abs(varA - varB), {'title': 'Yield variability', 'argument': f"Year-to-year production variability: {crop_a} var={varA:.2f}, {crop_b} var={varB:.2f}.", 'confidence': 0.5}))

    # 4. Drought-year resilience proxy: compare averages in low-rain years
    try:
        rain_mean = rain[rain['state'] == region]['avg_annual_rainfall'].mean()
        rain_std = rain[rain['state'] == region]['avg_annual_rainfall'].std()
        drought_thresh = rain_mean - max(0.1*rain_mean, rain_std)
        def drought_drop(df):
            if df.empty:
                return 0.0
            prod_by_year = df.groupby('year')['production'].sum()
            drought_years = [y for y in prod_by_year.index if (rain[(rain['state'] == region) & (rain['year'] == y)]['avg_annual_rainfall'].values.size>0 and rain[(rain['state'] == region) & (rain['year'] == y)]['avg_annual_rainfall'].values[0] < drought_thresh)]
            if not drought_years:
                return 0.0
            mean_drought = prod_by_year.loc[drought_years].mean() if len(drought_years)>0 else prod_by_year.mean()
            mean_all = prod_by_year.mean()
            return float((mean_all - mean_drought)/max(1, mean_all))
        dropA = drought_drop(cA)
        dropB = drought_drop(cB)
        candidates.append((abs(dropA - dropB), {'title': 'Drought-year resilience', 'argument': f"Relative production drop in drought years: {crop_a}={dropA:.2f}, {crop_b}={dropB:.2f} (lower is better).", 'confidence': 0.5}))
    except Exception:
        pass

    # Rank candidates by effect size and return top 3 with provenance and adjusted confidence
    candidates = sorted(candidates, key=lambda x: -x[0])[:3]
    args = []
    for score, cand in candidates:
        cand['provenance'] = prov
        # boost confidence if underlying series have sufficient years
        coverage = 0.0
        try:
            coverage = (min(len(cA['year'].dropna()), len(cB['year'].dropna()))/max(1, years))
        except Exception:
            coverage = 0.0
        cand['confidence'] = min(1.0, cand.get('confidence', 0.5) + 0.5*coverage)
        args.append(cand)

    return {'arguments': args[:3], 'provenance': prov}
