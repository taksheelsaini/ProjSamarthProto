import os
import pandas as pd

HERE = os.path.dirname(__file__)
# Use the normalized local CSVs only (no live API dependency)
SAMPLE_AGRI = os.path.normpath(os.path.join(HERE, '..', 'data', 'normalized_production_2018_19.csv'))
SAMPLE_RAIN = os.path.normpath(os.path.join(HERE, '..', 'data', 'normalized_rainfall_2018_19.csv'))


class DataGovClient:
    """I am a simple local-data client. I always load the normalized CSVs shipped in `data/`.

    I intentionally have no network dependency so my prototype is reproducible offline.
    """
    def get_agriculture_dataframe(self, resource_id=None):
        try:
            df = pd.read_csv(SAMPLE_AGRI, engine='python', on_bad_lines='skip')
        except Exception:
            # Return empty DataFrame on error; callers should handle defaults
            df = pd.DataFrame()
        meta = {
            'title': 'Normalized Agriculture data',
            'publisher': 'Local',
            'url': f'local://data/{os.path.basename(SAMPLE_AGRI)}',
        }
        return df, meta

    def get_rainfall_dataframe(self, resource_id=None):
        try:
            df = pd.read_csv(SAMPLE_RAIN, engine='python', on_bad_lines='skip')
        except Exception:
            df = pd.DataFrame()
        meta = {
            'title': 'Normalized Rainfall data',
            'publisher': 'Local',
            'url': f'local://data/{os.path.basename(SAMPLE_RAIN)}',
        }
        return df, meta
