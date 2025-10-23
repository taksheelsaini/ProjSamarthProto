import pandas as pd
import re

def normalize_agriculture(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    colmap = {}
    for c in df.columns:
        if 'state' in c:
            colmap[c] = 'state'
        if 'district' in c:
            colmap[c] = 'district'
        if c in ('year', 'yyyy'):
            colmap[c] = 'year'
        if 'crop' in c:
            colmap[c] = 'crop'
        if 'production' in c or 'prod' in c:
            colmap[c] = 'production_tonnes'
        if 'area' in c:
            colmap[c] = 'area'
        if 'season' in c:
            colmap[c] = 'season'
    df = df.rename(columns=colmap)
    if 'production_tonnes' in df.columns:
        col = df['production_tonnes']
        # If multiple columns were mapped to the same canonical name, pandas will return a DataFrame
        # when selecting by label; handle that by coercing each column and reducing to a single series.
        if isinstance(col, pd.DataFrame):
            df['production_tonnes'] = col.apply(pd.to_numeric, errors='coerce').sum(axis=1)
        else:
            df['production_tonnes'] = pd.to_numeric(col, errors='coerce')
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    for req in ['state','year','crop','production_tonnes']:
        if req not in df.columns:
            df[req] = None
    df['state'] = df['state'].astype(str).str.strip().str.title().fillna('Unknown')
    df['crop'] = df['crop'].astype(str).str.strip().str.lower().fillna('unknown')
    cols = ['state','district','year','crop','season','production_tonnes','area']
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols].copy()

def normalize_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # preserve original column names for station-detection before any renaming
    orig_cols = list(df.columns)
    orig_lower = [c.strip().lower() for c in orig_cols]

    # Detect wide per-station rainfall layouts using original column names (before any rename)
    station_cols_orig = [c for c in orig_cols if ('actual' in c.lower() and 'rain' in c.lower()) or c.lower().startswith('actual_rainfall')]
    if station_cols_orig:
        # Melt into long form using original station columns
        id_vars = [c for c in orig_cols if c not in station_cols_orig]
        long = df.melt(id_vars=id_vars, value_vars=station_cols_orig, var_name='station', value_name='rain_mm')
        # Clean station names
        long['station'] = long['station'].astype(str).str.replace('actual_rainfall_in_','', flags=re.IGNORECASE)
        long['station'] = long['station'].str.replace('_in_mm','', flags=re.IGNORECASE)
        long['station'] = long['station'].str.replace('_',' ').str.strip()
        # Try to extract year from id_vars: prefer 'month' (which often contains e.g. "June'2018").
        period_col = None
        # prefer month first, then period/peroid, then any other id_var
        for cand in ['month', 'period', 'peroid', 'mon']:
            for oc in id_vars:
                if oc.strip().lower() == cand:
                    period_col = oc
                    break
            if period_col:
                break
        if period_col is not None:
            yrs = long[period_col].astype(str).str.extract(r"(\d{4})", expand=False)
            if yrs.notna().any():
                long['year'] = pd.to_numeric(yrs, errors='coerce')
        # fallback: attempt to extract from any id_var column (stop at first successful column)
        if 'year' not in long.columns or long['year'].isna().all():
            for oc in id_vars:
                yrs = long[oc].astype(str).str.extract(r"(\d{4})", expand=False)
                if yrs.notna().any():
                    long['year'] = pd.to_numeric(yrs, errors='coerce')
                    break

        # Heuristic mapping: map known station substrings to a state (this CSV appears to be Tamil Nadu stations)
        def station_to_state(s: str) -> str:
            s = (s or '').lower()
            tn_subs = ['karur','aravakurichi','paramathi','anaipalyam','kulithalai','thogaimalai','kadavur','palaviduthi','mayanur','panchapatti']
            for sub in tn_subs:
                if sub in s:
                    return 'Tamil Nadu'
            return 'Unknown'

        long['state'] = long['station'].apply(station_to_state)
        long['rain_mm'] = pd.to_numeric(long['rain_mm'], errors='coerce')
        # Aggregate monthly station readings to annual per state-year (mean across stations and months)
        agg = long.groupby(['state','year'])['rain_mm'].mean().reset_index().rename(columns={'rain_mm':'rainfall_mm'})
        # Return canonical columns
        out = agg.copy()
        out['district'] = pd.NA
        out['month'] = pd.NA
        # Ensure column order
        return out[['state','district','year','month','rainfall_mm']]

    # If not a wide station layout, do conservative renaming and robustly combine rainfall columns
    colmap = {}
    for c in orig_cols:
        lc = c.strip().lower()
        if 'state' in lc:
            colmap[c] = 'state'
        if 'district' in lc:
            colmap[c] = 'district'
        if lc in ('year','yyyy'):
            colmap[c] = 'year'
        if 'month' in lc and 'month of' not in lc:
            colmap[c] = 'month'
        # map explicit rainfall-like columns, but avoid overbroad matching that collapses many unrelated columns
        if re.search(r'\brain\b', lc) or 'rainfall' in lc or lc.endswith('_mm') and 'rain' in lc:
            colmap[c] = 'rainfall_mm'
    df = df.rename(columns=colmap)
    # Find all columns that look like rainfall measurements
    rain_cols = [c for c in df.columns if 'rain' in c.lower()]
    if len(rain_cols) > 1:
        df['rainfall_mm'] = df[rain_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    elif len(rain_cols) == 1:
        df['rainfall_mm'] = pd.to_numeric(df[rain_cols[0]], errors='coerce')
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        # Some rainfall files encode the year inside a period/month column (e.g. "June'2018" or "June 2018").
        # Try to extract a 4-digit year from any column that looks like a period/month indicator.
        year_extracted = None
        for candidate in ['peroid', 'period', 'month', 'mon']:
            if candidate in df.columns:
                # attempt to extract 4-digit year
                yrs = df[candidate].astype(str).str.extract(r"(\d{4})", expand=False)
                if yrs.notna().any():
                    df['year'] = pd.to_numeric(yrs, errors='coerce')
                    year_extracted = True
                    break
        # As a last resort, check all columns for a 4-digit year anywhere in the text
        if year_extracted is None:
            for c in df.columns:
                yrs = df[c].astype(str).str.extract(r"(\d{4})", expand=False)
                if yrs.notna().any():
                    df['year'] = pd.to_numeric(yrs, errors='coerce')
                    year_extracted = True
                    break
    for req in ['state','year','rainfall_mm']:
        if req not in df.columns:
            df[req] = pd.NA
    df['state'] = df['state'].astype(str).str.strip().str.title().fillna('Unknown')
    cols = ['state','district','year','month','rainfall_mm']
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols].copy()

def join_agri_climate(agri_df, rain_df):
    merged = agri_df.merge(rain_df.groupby(['state','year']).rainfall_mm.mean().reset_index(), on=['state','year'], how='left')
    return merged
