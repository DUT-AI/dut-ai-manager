import os
import re
from pathlib import Path


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Simple stack-based parser to replace cast(Any, X) with X
    # because regex can't handle nested parentheses well.
    while "cast(Any," in content:
        start_idx = content.find("cast(Any,")
        if start_idx == -1:
            break

        # Find the matching closing parenthesis
        paren_count = 0
        content_start = start_idx + len("cast(Any,")

        # skip spaces after comma
        while content_start < len(content) and content[content_start].isspace():
            content_start += 1

        end_idx = -1
        for i in range(start_idx + len("cast(Any,"), len(content)):
            if content[i] == "(":
                paren_count += 1
            elif content[i] == ")":
                if paren_count == 0:
                    end_idx = i
                    break
                paren_count -= 1

        if end_idx != -1:
            # We found the matching parenthesis
            inside_content = content[content_start:end_idx].strip()
            # Replace the whole cast(...) with the inside_content
            content = content[:start_idx] + inside_content + content[end_idx + 1 :]
        else:
            # Malformed, break to avoid infinite loop
            break

    # Clean up imports
    content = re.sub(
        r"from typing import Any, cast\n", "from typing import Any\n", content
    )
    content = re.sub(
        r"from typing import cast, Any\n", "from typing import Any\n", content
    )
    content = re.sub(
        r"from typing import Any, List, Optional, cast\n",
        "from typing import Any, List, Optional\n",
        content,
    )
    content = re.sub(
        r"from typing import List, Optional, cast\n",
        "from typing import List, Optional\n",
        content,
    )
    content = re.sub(r"from typing import cast\n", "", content)

    # fix empty lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {filepath}")


def main():
    app_dir = Path(__file__).parent.parent
    for root, _, files in os.walk(app_dir):
        for file in files:
            if file.endswith(".py") and file != "remove_cast.py":
                process_file(os.path.join(root, file))


if __name__ == "__main__":
    main()
