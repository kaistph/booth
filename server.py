from __future__ import annotations

import json
import os
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent

def resolve_db_path() -> Path:
    env_value = os.environ.get("KULTURA_DB_PATH")
    if env_value:
        candidate = Path(env_value).expanduser()
        if not candidate.is_absolute():
            candidate = (BASE_DIR / candidate).resolve()
    else:
        candidate = BASE_DIR / "kultura.db"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


DB_PATH = resolve_db_path()
PORT = int(os.environ.get("PORT", 8000))

BOOTH_DATA = [
    {
        "id": "tumbang",
        "name": "Tumbang Preso",
        "description": "Knock down the lata with slippers in this classic Filipino street game.",
        "password": "preso2024",
    },
    {
        "id": "calamansi",
        "name": "Calamansi Relay",
        "description": "Balance a calamansi on a spoon and dash for your team!",
        "password": "whyareurunning7",
    },
    {
        "id": "baybayin",
        "name": "Baybayin Calligraphy",
        "description": "Write your name using the pre-colonial Baybayin script.",
        "password": "baybayink05",
    },
    {
        "id": "pamahiin",
        "name": "Pamahiin Quiz",
        "description": "Test your knowledge of Filipino superstitions and beliefs.",
        "password": "swerteak0",
    },
    {
        "id": "maskara",
        "name": "Maskara Making",
        "description": "Design a colorful mask inspired by the MassKara Festival.",
        "password": "maskar4rt",
    },
    {
        "id": "imahe",
        "name": "Imahe ,
        "description": "Pose with your maskara and post an instagram story tagging @kaist.one .",
        "password": "imah3h3",
    },
]

PUBLIC_BOOTH_DATA = [
    {key: booth[key] for key in ("id", "name", "description")}
    for booth in BOOTH_DATA
]


def init_db() -> None:
    DB_PATH.touch(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booth_id TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, booth_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def fetch_user_row(username: str) -> Optional[sqlite3.Row]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM users WHERE lower(username) = lower(?)",
            (username,),
        ).fetchone()


def build_user_payload(row: sqlite3.Row) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        completion_rows = conn.execute(
            "SELECT booth_id, completed FROM completions WHERE user_id = ?",
            (row["id"],),
        ).fetchall()
    completions: Dict[str, bool] = {}
    for completion in completion_rows:
        if completion["completed"]:
            completions[completion["booth_id"]] = True
    return {
        "name": row["name"],
        "username": row["username"],
        "email": row["email"],
        "completions": completions,
    }


def upsert_completion(user_id: int, booth_id: str, is_complete: bool) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO completions (user_id, booth_id, completed)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, booth_id)
            DO UPDATE SET completed = excluded.completed
            """,
            (user_id, booth_id, 1 if is_complete else 0),
        )
        conn.commit()


class BoothRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if parts[:2] == ["api", "booths"]:
            self.send_json({"booths": PUBLIC_BOOTH_DATA})
            return
        if parts[:2] == ["api", "users"] and len(parts) == 3:
            username = parts[2]
            row = fetch_user_row(username)
            if not row:
                self.send_json({"error": "User not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json({"user": build_user_payload(row)})
            return
        super().do_GET()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if parts[:2] == ["api", "register"]:
            self.handle_register()
            return
        if parts[:2] == ["api", "login"]:
            self.handle_login()
            return
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "users" and parts[3] == "completions":
            self.handle_completion_update(parts[2])
            return
        self.send_json({"error": "Endpoint not found"}, status=HTTPStatus.NOT_FOUND)

    def handle_register(self) -> None:
        payload = self.read_body()
        required = ["name", "username", "email", "password"]
        if any(not payload.get(field) for field in required):
            self.send_json({"error": "All fields are required."}, status=HTTPStatus.BAD_REQUEST)
            return
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            conflict = conn.execute(
                """
                SELECT * FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
                """,
                (payload["username"], payload["email"]),
            ).fetchone()
            if conflict:
                self.send_json(
                    {"error": "That username or email is already registered."},
                    status=HTTPStatus.CONFLICT,
                )
                return
            conn.execute(
                "INSERT INTO users (name, username, email, password) VALUES (?, ?, ?, ?)",
                (
                    payload["name"].strip(),
                    payload["username"].strip(),
                    payload["email"].strip(),
                    payload["password"].strip(),
                ),
            )
            conn.commit()
        row = fetch_user_row(payload["username"])
        self.send_json({"user": build_user_payload(row)}, status=HTTPStatus.CREATED)

    def handle_login(self) -> None:
        payload = self.read_body()
        username = payload.get("username", "").strip()
        password = payload.get("password", "").strip()
        if not username or not password:
            self.send_json({"error": "Username and password are required."}, status=HTTPStatus.BAD_REQUEST)
            return
        row = fetch_user_row(username)
        if not row or row["password"] != password:
            self.send_json({"error": "Invalid credentials."}, status=HTTPStatus.UNAUTHORIZED)
            return
        self.send_json({"user": build_user_payload(row)})

    def handle_completion_update(self, username: str) -> None:
        row = fetch_user_row(username)
        if not row:
            self.send_json({"error": "User not found."}, status=HTTPStatus.NOT_FOUND)
            return
        payload = self.read_body()
        booth_id = payload.get("boothId")
        booth_password = payload.get("boothPassword", "").strip()
        mark_complete = bool(payload.get("completed"))
        if not booth_id or not booth_password:
            self.send_json({"error": "Booth ID and password are required."}, status=HTTPStatus.BAD_REQUEST)
            return
        booth = next((b for b in BOOTH_DATA if b["id"] == booth_id), None)
        if not booth:
            self.send_json({"error": "Booth not found."}, status=HTTPStatus.NOT_FOUND)
            return
        if booth_password != booth["password"]:
            self.send_json({"error": "Incorrect booth password."}, status=HTTPStatus.FORBIDDEN)
            return
        upsert_completion(row["id"], booth_id, mark_complete)
        self.send_json({"user": build_user_payload(row)})

    def read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length) if length else b""
        if not data:
            return {}
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    init_db()
    os.chdir(BASE_DIR)
    server = ThreadingHTTPServer(("", PORT), BoothRequestHandler)
    print(f"Using database at {DB_PATH}")
    print(f"Serving Kultura Quest on http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
