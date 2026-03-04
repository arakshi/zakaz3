import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    root = Path(__file__).resolve().parent
    app_path = root / "app.py"
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        "8501",
        "--browser.gatherUsageStats",
        "false",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
