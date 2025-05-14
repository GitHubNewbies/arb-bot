import os

APP_ENV = os.getenv("APP_ENV", "unknown").lower()

def main():
    print(f"[{APP_ENV.upper()}] Starting bot instance...")

    # Future logic: run engine or strategy
    # from src.engine import run_engine
    # run_engine()

if __name__ == "__main__":
    main()
