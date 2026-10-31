# Quickstart & Verification Guide: Modular Meeting Sub-modules

**Feature Branch**: `037-modular-meeting`  
**Date**: 2026-10-31  

---

## 1. Prerequisites

- Python 3.12+ with `uv` package manager installed.
- PostgreSQL running locally with applied migrations up to head (`038_fix_participant_timestamptz`).
- Node.js 20+ with npm dependencies installed in `frontend/`.

---

## 2. Validation Scenarios

### Step 1: Verify Code Formatting & Static Analysis
Run Ruff linter to verify zero circular imports, proper import ordering, and no line-length violations:
```bash
uv run --directory backend ruff check app/meeting/
```
*Expected Outcome*: `All checks passed!`

---

### Step 2: Verify Unit Tests for Modular Domain & Use Cases
Run isolated domain and use case unit tests:
```bash
uv run --directory backend pytest \
  tests/unit/test_meeting_domain.py \
  tests/unit/test_meeting_evaluation.py \
  tests/unit/test_meeting_use_cases.py \
  tests/unit/test_change_meeting_permission_request.py
```
*Expected Outcome*: All test cases pass 100%.

---

### Step 3: Verify API Routing & End-to-End Meeting Endpoints
Run the API integration tests against the modular composite router:
```bash
uv run --directory backend pytest tests/api/test_change_meeting_api.py
```
*Expected Outcome*: 100% pass on API contracts and permission checks.

---

### Step 4: Verify Frontend Build Health
Ensure TypeScript typings and frontend components function seamlessly with modular endpoints:
```bash
npm --prefix frontend run build
```
*Expected Outcome*: Build succeeds with zero TypeScript compilation errors.
