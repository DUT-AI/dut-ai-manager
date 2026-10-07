from sqlalchemy import select

from app.permission_request.infrastructure.model import PermissionRequest
from app.shared.infrastructure.database import get_session


def main():
    for session in get_session():
        stmt = select(PermissionRequest).where(
            PermissionRequest.id.in_([127, 128, 130])
        )
        rows = session.scalars(stmt).all()
        for r in rows:
            print(
                f"Row {r.id}: hw={r.homework_id}, category={r.category}, created_by={r.created_by}"
            )
            e = r.to_entity()
            print(
                f"Entity: hw={e.homework_id}, created_by={e.created_by}, user_id={e.user_id}"
            )
        return


if __name__ == "__main__":
    main()
