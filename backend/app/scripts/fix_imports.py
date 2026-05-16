import re

files_to_fix = [
    "app/billing/schemas.py",
    "app/homework/application/event_handlers.py",
    "app/meeting/application/event_handlers.py",
    "app/meeting/infrastructure/repository.py",
    "app/permission_request/application/use_cases.py",
    "app/user/application/use_cases.py",
]


def add_cast_import(filepath):
    with open(filepath) as f:
        content = f.read()

    if "from typing import cast" not in content and "from typing import" in content:
        content = re.sub(r"(from typing import [^\n]+)", r"\1, cast", content, count=1)
    elif "from typing import cast" not in content:
        content = "from typing import cast\n" + content

    with open(filepath, "w") as f:
        f.write(content)


for file in files_to_fix:
    add_cast_import(file)

# Fix event_bus.py
with open("app/shared/domain/event_bus.py") as f:
    content = f.read()
content = content.replace(
    "await instance.handle(event)", "await instance.handle(event)  # type: ignore"
)
with open("app/shared/domain/event_bus.py", "w") as f:
    f.write(content)
