import re

def extract_candidates(text):
    patterns = [
        r"(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./{}:-]+)",
        r"(GET|POST|PUT|PATCH|DELETE)\s*\n\s*(/[A-Za-z0-9_./{}:-]+)",
        r"(get|post|put|patch|delete)[`'\"\s]+(/v\d+/[A-Za-z0-9_./{}:-]+)",
        r"(?<!['\"/\w])(/v\d+/[A-Za-z0-9_./{}:-]{4,})",
    ]

    seen = set()
    unique = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            groups = match.groups()
            if len(groups) == 2:
                method = groups[0].upper()
                path = groups[1]
            else:
                method = "?"   # path found but method unclear
                path = groups[0]

            key = (method, path)
            if key not in seen:
                seen.add(key)
                unique.append({"method": method, "path": path})

    return unique