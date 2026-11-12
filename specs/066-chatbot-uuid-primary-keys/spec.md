# Feature Specification: Chatbot UUID Primary Keys Migration

**Feature Number**: 066
**Status**: In Planning
**Date**: 2026-11-12

## 1. Overview & Problem Statement
Hiện tại, các bảng liên quan đến tính năng Chatbot (`chat_sessions` và `chat_messages`) đang sử dụng khóa chính dạng số nguyên tự tăng (`SQLAlchemyIntPrimaryKeyMixin` với kiểu `Integer`).
Theo định hướng kiến trúc hiện đại của dự án (tương tự như trong `SQLAlchemyUuidPrimaryKeyMixin` và RFC 9562 UUIDv7), toàn bộ các bảng chatbot cần chuyển đổi sang dùng `UUID` (UUIDv7) làm Primary Key và Foreign Key:
- `chat_sessions.id`: chuyển từ `Integer` sang `UUID`
- `chat_messages.id`: chuyển từ `Integer` sang `UUID`
- `chat_messages.session_id`: chuyển từ `Integer` sang `UUID` (Foreign Key trỏ đến `chat_sessions.id`)

**Chấp thuận của người dùng**: Xóa bỏ toàn bộ dữ liệu lịch sử chat hiện tại (drop/truncate tables) để thực hiện migration sạch sẽ, không cần bảo lưu dữ liệu cũ.

## 2. Requirements & Scope

### Functional Requirements
- **FR-01**: Cập nhật ORM models `ChatSessionModel` và `ChatMessageModel` kế thừa `SQLAlchemyUuidPrimaryKeyMixin` thay cho `SQLAlchemyIntPrimaryKeyMixin`.
- **FR-02**: Cập nhật `session_id` trong `ChatMessageModel` thành `UUID` trỏ tới `chat_sessions.id`.
- **FR-03**: Cập nhật Domain Entities `ChatSession(BaseGenericEntity[UUID])` và `ChatMessage(BaseGenericEntity[UUID])`.
- **FR-04**: Cập nhật các schemas/DTOs Pydantic: `session_id` và `id` thành kiểu `UUID`.
- **FR-05**: Cập nhật Controller và Use Cases nhận và trả về `UUID` (hoặc `UUID4`/`UUID` tương thích).
- **FR-06**: Tạo Alembic migration mới: xóa bảng cũ (hoặc drop cascade) và tạo lại 2 bảng với kiểu cột `UUID` (PostgreSQL `uuid`).
- **FR-07**: Cập nhật Frontend types (`ChatMessage`, `ChatSession`, service, hooks, components) chấp nhận `sessionId: string | null` (UUID string) thay vì `number`.
- **FR-08**: Cập nhật tất cả unit tests của chatbot sang UUID.

### Non-Functional Requirements
- **NFR-01**: Tuân thủ chuẩn UUIDv7 của hệ thống (`app.shared.domain.uuid_utils.uuid7`).
- **NFR-02**: Không làm vỡ cấu trúc clean architecture và OpenAPI schema contracts.
