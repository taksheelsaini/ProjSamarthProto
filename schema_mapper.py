"""Schema mapper: heuristics to map dataset columns to canonical names used by the QA engine.

Canonical fields: state, district, year, crop, production, avg_annual_rainfall
This module provides:
- map_schema(df): returns (df_mapped, mapping)
- extract_provenance_rows(df, filters): helper to return selected rows for provenance
"""
from typing import Tuple, Dict, Any
import pandas as pd
import difflib
try:
    from codebook_parser import guess_and_apply
except Exception:
    # If codebook_parser is not present (we removed live-fetch helpers), provide a noop fallback.
    def guess_and_apply(df):
        return df
import hashlib

CANONICAL = ['state','district','year','crop','production','avg_annual_rainfall']

# common aliases mapped to canonical fields
ALIASES = {
    'state': ['state_name','state','st_name','statecode','state_name'],
    'district': ['district','district_name','dist_name','districtcode'],
    'year': ['year','yr','season','financial_year'],
    'crop': ['crop','crop_name','cropcode','cropname'],
    'production': ['production','production_tonnes','qty','production_quantity','production_in_tonnes','production_in_qtls'],
    'avg_annual_rainfall': ['rainfall','avg_annual_rainfall','annual_rainfall','rain_mm']
}


def _best_alias(col: str) -> Tuple[str,float]:
    """Return best canonical match for column name and a score."""
    col_l = col.lower().replace(' ','_')
    best = (None,0.0)
    for canon, aliases in ALIASES.items():
        for a in aliases:
            if col_l == a:
                return canon, 1.0
            # fuzzy match
            score = difflib.SequenceMatcher(None, col_l, a).ratio()
            if score > best[1]:
                best = (canon, score)
    return best


def map_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str,str]]:
    """Map df columns to canonical names when possible. Returns (df_mapped, mapping).

    Mapping contains canonical_field -> original_column_name.
    """
    mapping: Dict[str,str] = {}
    # best-effort apply codebooks before mapping
    try:
        df = guess_and_apply(df)
    except Exception:
        pass

    cols = list(df.columns)
    used = set()
    for c in cols:
        canon, score = _best_alias(c)
        if canon and score > 0.6 and canon not in mapping:
            mapping[canon] = c
            used.add(c)

    # If year not found, try to detect integer-like column with limited range
    if 'year' not in mapping:
        for c in cols:
            if c in used: continue
            if df[c].dropna().apply(lambda v: isinstance(v,int) or (isinstance(v,str) and v.isdigit())).all():
                mapping['year'] = c
                used.add(c)
                break

    # Build new df with canonical columns (where available). Also add a stable row id.
    out = pd.DataFrame()
    for canon in CANONICAL:
        orig = mapping.get(canon)
        if orig and orig in df.columns:
            out[canon] = df[orig]
        else:
            out[canon] = pd.NA

    # create a stable row id combining a checksum of row values to help provenance
    def _row_checksum(row_values) -> str:
        m = hashlib.sha1()
        # join stringified values with | for deterministic checksum
        m.update('|'.join([str(x) for x in row_values]).encode('utf-8'))
        return m.hexdigest()

    try:
        checksums = out.apply(lambda r: _row_checksum(r.values.tolist()), axis=1)
        out['__row_id'] = checksums
    except Exception:
        out['__row_id'] = pd.Series([None]*len(out))

    return out, mapping


def extract_provenance_rows(df: pd.DataFrame, filters: Dict[str,Any], max_rows:int=10) -> pd.DataFrame:
    """Return subset of df matching filters for provenance display.

    Filters example: {'state':'State_X','year':[2020,2021]}
    """
    sel = df
    for k,v in filters.items():
        if k not in df.columns:
            continue
        if isinstance(v, list):
            sel = sel[sel[k].isin(v)]
        else:
            sel = sel[sel[k]==v]
    # ensure __row_id exists; if not, generate a fallback based on index
    if '__row_id' not in sel.columns:
        sel = sel.copy()
        sel['__row_id'] = sel.index.astype(str)
    out = sel.head(max_rows)
    # add a simple permalink field if dataset_url provided in filters
    ds_url = filters.get('dataset_url') if isinstance(filters, dict) else None
    if ds_url:
        out = out.copy()
        out['__permalink'] = out['__row_id'].apply(lambda rid: f"{ds_url}#row={rid}")
    return out
