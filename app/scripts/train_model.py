# app/scripts/train_model.py

from app.services.forecast_service import train_all_models


def main() -> None:
    results = train_all_models()
    for r in results:
        print(r)

    print("All models trained")


if __name__ == "__main__":
    main()
