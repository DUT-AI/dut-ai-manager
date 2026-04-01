"""
Test script to manually run the homework checker job.

Usage:
    cd backend
    python -m tests.test_homework_checker
"""

import asyncio

# Import __init__ first to setup sys.path
import tests  # noqa: F401
from app.jobs.homework_checker_job import check_overdue_homework_submissions


async def main():
    print("=" * 60)
    print("🧪 Testing Homework Checker Job")
    print("=" * 60)

    await check_overdue_homework_submissions()

    print("=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
