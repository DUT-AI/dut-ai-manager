# Quickstart Guide: Kiểm thử Khóa chính UUID và Tách biệt Soft Delete

**Feature**: `059-uuid-optional-soft-delete`  
**Date**: 2026-11-10  
**Status**: Ready for Verification  

---

## 1. Mục tiêu Kiểm thử

Chứng minh rằng hệ thống đáp ứng trọn vẹn các yêu cầu:
1. Sinh mã định danh UUIDv7 tuần tự theo thời gian và lưu trữ chính xác vào cơ sở dữ liệu.
2. Domain Entity và ORM Model mới hoạt động với khóa chính UUIDv7 mượt mà qua BaseRepository.
3. Model không có cờ `is_deleted` thực hiện các câu lệnh `get_all`, `get_paged`, `get_by_id` mà không sinh điều kiện SQL `WHERE is_deleted = false`.
4. Gọi `soft_delete()` trên model không có `is_deleted` sẽ ném ngoại lệ rõ ràng (`NotImplementedError`).
5. Gọi `hard_delete()` trên cả model có và không có `is_deleted` sẽ xóa sạch bản ghi vật lý.
6. 100% các test hiện hữu của các domain cũ (`tests/unit/` và `tests/api/`) tiếp tục vượt qua mà không có lỗi hồi quy (Zero Regressions).

---

## 2. Kịch bản Kiểm thử Tự động (Automated Unit Tests)

Bộ unit test chuyên biệt sẽ được đặt tại:  
`backend/tests/unit/test_uuid_and_optional_soft_delete.py`

### 2.1. Kiểm tra Sinh mã UUIDv7 (`test_uuid7_generation`)
- Gọi `uuid7()` liên tiếp 100 lần.
- Đảm bảo version luôn là 7 (`u.version == 7`).
- Đảm bảo tính tuần tự tăng dần theo thời gian (`u[i] < u[i+1]`).

### 2.2. Kiểm tra Model UUID không có Xóa mềm (`test_uuid_model_without_soft_delete`)
- Tạo test model kế thừa `(SQLAlchemyUuidPrimaryKeyMixin, SQLAlchemyTimestampMixin, Base)`.
- Tạo test entity kế thừa `BaseUuidEntity`.
- Thêm bản ghi mới -> Kiểm tra `id` được sinh tự động dạng UUIDv7.
- Truy vấn `get_by_id(uuid)` -> Trả về đúng entity.
- Truy vấn `get_all()` và `get_paged()` -> Trả về đúng bản ghi, không lỗi `AttributeError` do thiếu `is_deleted`.
- Gọi `soft_delete(uuid)` -> Ném `NotImplementedError`.
- Gọi `hard_delete(uuid)` -> Bản ghi bị xóa vật lý, `get_by_id(uuid)` trả về `None`.

### 2.3. Kiểm tra Model UUID có Xóa mềm (`test_uuid_model_with_soft_delete`)
- Tạo test model kế thừa `(SQLAlchemyUuidPrimaryKeyMixin, SQLAlchemyTimestampMixin, SQLAlchemySoftDeleteMixin, Base)`.
- Tạo test entity kế thừa `(BaseUuidEntity, SoftDeleteEntityMixin)`.
- Thêm bản ghi mới -> Gọi `soft_delete(uuid)` -> `is_deleted = True`.
- Gọi `get_by_id(uuid)` -> Trả về `None` do đã bị lọc xóa mềm.
- Gọi `get_all()` -> Không chứa bản ghi đã xóa mềm.
- Gọi `hard_delete(uuid)` -> Bản ghi bị xóa vĩnh viễn khỏi database.

### 2.4. Kiểm tra Tương thích ngược Model cũ (`test_legacy_model_backward_compatibility`)
- Kiểm tra các model cũ kế thừa `BaseEntity` và `SQLAlchemyTimestampMixin` vẫn hoạt động với `id: int` và `is_deleted: bool`.

---

## 3. Lệnh chạy Kiểm thử

```bash
# 1. Chạy unit test chuyên biệt cho tính năng mới
cd backend
uv run pytest tests/unit/test_uuid_and_optional_soft_delete.py -v

# 2. Chạy toàn bộ test suite hiện hữu để đảm bảo không hồi quy
uv run pytest
```
