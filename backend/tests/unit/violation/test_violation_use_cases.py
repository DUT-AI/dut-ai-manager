from unittest.mock import MagicMock

from app.violation.application import BulkDeleteViolationsUseCase, GetViolationsUseCase


def test_bulk_delete_violations():
    mock_repo = MagicMock()
    mock_repo.bulk_delete.return_value = 3
    uc = BulkDeleteViolationsUseCase(mock_repo)

    result = uc.execute([1, 2, 3])

    mock_repo.bulk_delete.assert_called_once_with([1, 2, 3])
    assert result == 3


def test_bulk_delete_violations_empty():
    mock_repo = MagicMock()
    uc = BulkDeleteViolationsUseCase(mock_repo)

    result = uc.execute([])

    mock_repo.bulk_delete.assert_not_called()
    assert result == 0


def test_get_by_month_with_user_id_only():
    mock_repo = MagicMock()
    uc = GetViolationsUseCase(mock_repo)

    uc.get_by_month(user_id=5)

    mock_repo.get_by_month.assert_called_once_with(
        month=None,
        year=None,
        user_id=5,
        start_date=None,
        end_date=None,
    )


def test_get_by_month_with_no_params():
    mock_repo = MagicMock()
    uc = GetViolationsUseCase(mock_repo)

    uc.get_by_month()

    mock_repo.get_by_month.assert_called_once()
    call_kwargs = mock_repo.get_by_month.call_args.kwargs
    assert call_kwargs["month"] is not None
    assert call_kwargs["year"] is not None
    assert call_kwargs["user_id"] is None


if __name__ == "__main__":
    test_bulk_delete_violations()
    test_bulk_delete_violations_empty()
    test_get_by_month_with_user_id_only()
    test_get_by_month_with_no_params()
    print("All violation use case tests passed!")
