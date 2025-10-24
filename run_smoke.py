"""Simple smoke test runner for my Project Samarth.

I load sample evidence, normalize it, run the generator, and print results.
"""
from normalization import normalize_evidence, provenance_score
from generator import generate_policy_argument
import os


def main():
    # Construct a minimal sample evidence set from the two normalized CSV filenames.
    # I avoid relying on an extra sample JSON file and keep the smoke test self-contained.
    data = [
        {"date": "2024-06-01", "source": "local://data/normalized_production_2018_19.csv", "headline": "Production signal from normalized production dataset", "relevance": 8},
        {"date": "2023-09-15", "source": "local://data/normalized_rainfall_2018_19.csv", "headline": "Rainfall signal from normalized rainfall dataset", "relevance": 7},
    ]

    norm = normalize_evidence(data)
    args = generate_policy_argument("Should we expand subsidized irrigation in region X?", norm, top_k=4)

    print("Generated arguments:\n")
    for i,a in enumerate(args, start=1):
        print(f"{i}. {a['title']}")
        print(a['argument'])
        print(f"Provenance: {a['provenance']:.2f} — Sources: {a['sources']}\n")

    print("Aggregate provenance:", provenance_score(args))


if __name__ == '__main__':
    main()
