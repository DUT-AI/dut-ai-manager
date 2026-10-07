from sqlalchemy import select

from app.shared.infrastructure.database import get_session
from app.violation.infrastructure.model import ViolationModel


def main():
    for session in get_session():
        stmt = select(ViolationModel).where(ViolationModel.user_id.in_([13, 15, 12]))
        violations = session.scalars(stmt).all()
        for v in violations:
            print(
                f"Violation - User: {v.user_id}, Date: {v.date}, Reason: {v.reason}, Created_at: {v.created_at}"
            )
        return


if __name__ == "__main__":
    main()
