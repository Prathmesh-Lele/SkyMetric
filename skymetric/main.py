"""CLI entry point for the SkyMetric system."""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def cmd_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    from skymetric.api.main import app
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_dashboard(args):
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])


def cmd_seed(args):
    """Generate and store seed data in the database."""
    from datetime import datetime, timedelta
    from skymetric.models.database import init_db, SessionLocal
    from skymetric.models.fare import Fare
    from skymetric.data.seed_data import generate_30_day_seed

    init_db()
    db = SessionLocal()

    print(f"Generating {args.days} days of seed data...")
    records = generate_30_day_seed(
        end_date=datetime.utcnow(),
        include_outliers=not args.clean,
    )

    for r in records:
        fare = Fare(
            timestamp=r["timestamp"],
            origin=r["origin"],
            destination=r["destination"],
            carrier=r["carrier"],
            flight_number=r["flight_number"],
            departure_time=r["departure_time"],
            advance_window_days=r["advance_window_days"],
            fare_class=r["fare_class"],
            base_fare=r["base_fare"],
            taxes_and_fees=r["taxes_and_fees"],
            udf=r.get("udf"),
            convenience_charge=r.get("convenience_charge"),
            total_fare=r["total_fare"],
            source_platform=r["source_platform"],
        )
        db.add(fare)

    db.commit()
    db.close()
    print(f"Seeded {len(records)} fare records.")


def cmd_test(args):
    """Run the test suite."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "skymetric/tests/", "-v", "--tb=short"],
        cwd=str(Path(__file__).parent.parent),
    )
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="SkyMetric - India Airfare Price Index System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.set_defaults(func=cmd_serve)

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Launch the Streamlit dashboard")
    dash_parser.set_defaults(func=cmd_dashboard)

    # seed
    seed_parser = subparsers.add_parser("seed", help="Generate seed data")
    seed_parser.add_argument("--days", type=int, default=30)
    seed_parser.add_argument("--clean", action="store_true", help="Exclude outliers")
    seed_parser.set_defaults(func=cmd_seed)

    # test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.set_defaults(func=cmd_test)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
