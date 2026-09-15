"""Draft session repository for crash/restart recovery."""

from typing import Optional
from sqlalchemy.orm import Session
from app.database.models.draft import CreationDraft

class DraftRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[CreationDraft]:
        return db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()

    @staticmethod
    def create_or_update(
        db: Session,
        user_id: int,
        quiz_id: int,
        state: str = "WAITING_TITLE"
    ) -> CreationDraft:
        draft = db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()
        if draft:
            draft.quiz_id = quiz_id
            draft.state = state
            draft.pending_media_file_id = None
            draft.pending_media_type = None
        else:
            draft = CreationDraft(
                user_id=user_id,
                quiz_id=quiz_id,
                state=state
            )
            db.add(draft)
        db.flush()
        return draft

    @staticmethod
    def update_state(db: Session, user_id: int, new_state: str) -> Optional[CreationDraft]:
        draft = db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()
        if draft:
            draft.state = new_state
            db.flush()
        return draft

    @staticmethod
    def set_pending_media(
        db: Session,
        user_id: int,
        media_file_id: str,
        media_type: str
    ) -> Optional[CreationDraft]:
        draft = db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()
        if draft:
            draft.pending_media_file_id = media_file_id
            draft.pending_media_type = media_type
            db.flush()
        return draft

    @staticmethod
    def clear_pending_media(db: Session, user_id: int) -> None:
        draft = db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()
        if draft:
            draft.pending_media_file_id = None
            draft.pending_media_type = None
            db.flush()

    @staticmethod
    def delete_by_user_id(db: Session, user_id: int) -> bool:
        draft = db.query(CreationDraft).filter(CreationDraft.user_id == user_id).first()
        if draft:
            db.delete(draft)
            db.flush()
            return True
        return False
