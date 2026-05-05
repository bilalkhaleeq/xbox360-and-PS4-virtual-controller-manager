import sys
import re

def categorize_message(msg):
    # Don't prefix if it's already prefixed
    if re.match(r'^(feat|fix|docs|refactor|chore|style|test|build|ci)(\(.*\))?!?: ', msg.lower()):
        return msg

    # Keyword mapping with priority (First match wins)
    # Stems are used to match multiple forms (e.g., 'creat' matches create, created, creating)
    rules = [
        (r'\b(feat|add|new|implement|allow|creat|introduct|provid)', 'feat'),
        (r'\b(fix|resolv|bug|patch|issue|prevent|avoid|correct)', 'fix'),
        (r'\b(ci|workflow|github|action|yaml|yml|pipeline|devops)', 'ci'),
        (r'\b(doc|readme|comment|manual|help|guide|wiki|developer|markdown|\.md)', 'docs'),
        (r'\b(test|unit|pyt|check|verify|validat)', 'test'),
        (r'\b(style|format|lint|prettier|css|ui|ux)', 'style'),
        (r'\b(build|version|bump|pkg|packag|dist)', 'build'),
        (r'\b(refactor|clean|simplif|organiz|struct|renam|improv|polish|adjust|modif)', 'refactor'),
        (r'\b(updat|chang|sync)', 'chore'),
    ]

    for pattern, prefix in rules:
        if re.search(pattern, msg.lower()):
            return f"{prefix}: {msg}"

    # Default to chore or leave as is if no clear match
    return f"chore: {msg}"

if __name__ == "__main__":
    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, 'r') as f:
        content = f.read()

    # Skip if it's a merge commit or other system message
    if content.startswith('Merge ') or content.startswith('#'):
        sys.exit(0)

    new_content = categorize_message(content.strip())

    with open(commit_msg_filepath, 'w') as f:
        f.write(new_content)
