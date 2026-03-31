# app/scripts/build_features.py

from app.services.feature_service import build_features

def main() -> None:
    rows = build_features()
    print(f"Feature store built: {rows} rows written")

if __name__ == "__main__":
    main()