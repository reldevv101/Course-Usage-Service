from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def main() -> None:
    username = input("Admin username: ").strip().lower()
    if len(username) < 3 or len(username) > 50:
        raise SystemExit("Username must be 3-50 characters")
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must have at least 12 characters")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)):
            raise SystemExit("That username already exists")
        db.add(User(username=username, password_hash=hash_password(password), role="admin", student_id=None, is_active=True))
        db.commit()
    print("Admin account created. Keep the credentials private.")


if __name__ == "__main__":
    main()
