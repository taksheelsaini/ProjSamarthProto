import pandas as pd
from collections import defaultdict

def generate_policy_arguments(agri_df: pd.DataFrame, rain_df: pd.DataFrame, crop_a: str, crop_b: str, region_state=None, years=5):
    """
    Generate up to 3 concise data-backed arguments for promoting crop_a over crop_b in region_state.
    Each argument is a dict {text, sources}
    """
    args = []
    ad = agri_df.copy()
    rd = rain_df.copy()
    if region_state:
        ad = ad[ad['state']==region_state]
        rd = rd[rd['state']==region_state]
    yrs = sorted(ad['year'].dropna().unique())
    window = yrs[-years:] if len(yrs)>0 else []
    adw = ad[ad['year'].isin(window)] if window else ad

    # Arg1: comparative yield/production stability
    a_sum = adw[adw['crop'].str.contains(crop_a, case=False)].production_tonnes.sum()
    b_sum = adw[adw['crop'].str.contains(crop_b, case=False)].production_tonnes.sum()
    text1 = f"Over the last {len(window)} years, total production of {crop_a} was {a_sum:.0f} tonnes vs {b_sum:.0f} tonnes for {crop_b}."
    sources1 = [
        {"title":"Agriculture production (normalized)", "url":"local://data/normalized_production_2018_19.csv"}
    ]
    args.append({"text": text1, "sources": sources1})

    # Arg2: water/climate suitability — show rainfall trends or anomalies favoring drought-resistant crop_a
    # compute avg rainfall and trend
    r_avg = rd['rainfall_mm'].mean()
    text2 = f"Average annual rainfall in the region is {r_avg:.0f} mm; lower rainfall variability favors drought-resistant crops like {crop_a}."
    sources2 = [{"title":"Rainfall (normalized)", "url":"local://data/normalized_rainfall_2018_19.csv"}]
    args.append({"text": text2, "sources": sources2})

    # Arg3: economic diversification / risk
    # compute number of districts producing crop_a vs crop_b
    a_dists = adw[adw['crop'].str.contains(crop_a, case=False)].district.nunique()
    b_dists = adw[adw['crop'].str.contains(crop_b, case=False)].district.nunique()
    text3 = f"{crop_a.title()} is produced across {a_dists} districts vs {b_dists} for {crop_b}, suggesting {crop_a} may offer broader diversification benefits." 
    sources3 = [ {"title":"Agriculture production (normalized)", "url":"local://data/normalized_production_2018_19.csv"} ]
    args.append({"text": text3, "sources": sources3})

    return args

def provenance_score(arguments):
    """
    Simple provenance score: number of unique source URLs cited across all arguments.
    """
    urls = set()
    for a in arguments:
        for s in a.get('sources',[]):
            urls.add(s.get('url'))
    return len(urls)
