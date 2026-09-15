"""User repository."""

from typing import Optional
from sqlalchemy.orm import Session
from app.database.models.user import User

class UserRepository:
    @staticmethod
    def get_or_create(
        db: Session,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        if not user:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name
            )
            db.add(user)
            db.flush()
        else:
            # Update user info if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if updated:
                db.flush()
        return user

    @staticmethod
    def get_by_telegram_id(db: Session, telegram_user_id: int) -> Optional[User]:
        return db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    @staticmethod
    def set_language(db: Session, telegram_user_id: int, lang_code: str) -> None:
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        if user:
            user.language_code = lang_code
            db.flush()
