"""Personalization — user profile manage karta hai."""


def get_or_create_user(name: str = None, city: str = None, course: str = None) -> int:
    from backend.database import db_execute, DB_AVAILABLE
    if not DB_AVAILABLE:
        return 1
    try:
        if name:
            row = db_execute("SELECT id FROM users WHERE name=?", (name,), fetch='one')
            if row:
                return row["id"]
        uid = db_execute(
            "INSERT INTO users (name, city, interested_course) VALUES (?,?,?)",
            (name, city, course)
        )
        return uid or 1
    except Exception as e:
        print(f"[Personalization] Error: {e}")
        return 1


def get_user_info(user_id: int) -> dict:
    from backend.database import db_execute, DB_AVAILABLE
    if not DB_AVAILABLE:
        return {}
    try:
        row = db_execute("SELECT * FROM users WHERE id=?", (user_id,), fetch='one')
        if row:
            return {
                "name": row["name"],
                "city": row["city"],
                "course": row["interested_course"],
                "language": row["language_preference"],
            }
        return {}
    except Exception as e:
        print(f"[Personalization] Error: {e}")
        return {}
