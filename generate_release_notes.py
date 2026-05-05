import subprocess
import datetime
import re

def get_last_tag():
    try:
        # We look for the latest tag reachable from the parent of the current commit.
        # This ensures that if we are currently at a tag (e.g. v1.1.0), 
        # we find the one BEFORE it (e.g. v1.0.0).
        return subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0', 'HEAD^'], stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_commits(since_tag):
    # Fetch Hash, Date, Message AND changed files
    git_cmd = ['git', 'log', f'{since_tag}..HEAD', '--pretty=format:COMMIT:%H|%ad|%s', '--name-only', '--date=format:%Y-%m-%d %H:%M']
    if not since_tag:
        git_cmd = ['git', 'log', '--pretty=format:COMMIT:%H|%ad|%s', '--name-only', '--date=format:%Y-%m-%d %H:%M']
    
    output = subprocess.check_output(git_cmd).decode().strip()
    if not output:
        return []

    commits = []
    current_commit = None
    
    for line in output.split('\n'):
        if line.startswith('COMMIT:'):
            if current_commit:
                commits.append(current_commit)
            parts = line[7:].split('|')
            current_commit = {
                'hash': parts[0],
                'date': parts[1],
                'message': parts[2],
                'files': []
            }
        elif line.strip():
            current_commit['files'].append(line.strip())
            
    if current_commit:
        commits.append(current_commit)
        
    return commits

def generate_notes():
    last_tag = get_last_tag()
    all_commits = get_commits(last_tag)
    
    if not all_commits:
        return "No changes since last release."

    # Only include these categories in the final release notes
    target_categories = {
        "🚀 Features": [],
        "🐞 Bug Fixes": [],
        "🛠️ Refactors": []
    }

    mappings = {
        'feat': "🚀 Features",
        'fix': "🐞 Bug Fixes",
        'refactor': "🛠️ Refactors"
    }

    # Configuration for File-Aware Intelligence
    APP_FILES = ['virtual_controller.py']
    NOISE_DIRS = ['.github/', '.githooks/']
    NOISE_FILES = ['README.md', 'DEVELOPER.md', 'generate_release_notes.py', '.gitignore', 'requirements.txt', 'controller_config.json']

    # Deep-content keywords for sub-item filtering
    noise_keywords = ['ci', 'workflow', 'github', 'action', 'pipeline', 'devops', 'doc', 'readme', 'comment', 'manual', 'help', 'guide', 'wiki', 'build', 'package', 'dist', 'release', 'version', 'bump']
    app_keywords = ['logic', 'fix', 'bug', 'feat', 'add', 'new', 'resolv', 'prevent', 'controller', 'gamepad', 'binding', 'key', 'ps4', 'xbox', 'connection', 'driver', 'emulat', 'ui', 'gui', 'safety', 'conflict']

    for commit in all_commits:
        # --- LAYER 1: File-Aware Filtering ---
        # A commit is relevant only if it touched an App File 
        # OR touched something NOT in the noise list.
        is_app_relevant = False
        for file in commit['files']:
            is_noise = any(file.startswith(d) for d in NOISE_DIRS) or (file in NOISE_FILES)
            if not is_noise:
                is_app_relevant = True
                break
        
        if not is_app_relevant:
            continue

        # --- LAYER 2: Conventional Prefix Filtering ---
        message = commit['message']
        match = re.match(r'^(\w+)(\(.*\))?!?: (.*)$', message)
        if not match: continue
            
        prefix = match.group(1).lower()
        full_body = match.group(3)
        category = mappings.get(prefix)
        
        if category not in target_categories:
            continue

        # --- LAYER 3: Intelligent Deep-Content Filtering ---
        parts = re.split(r'[,;\n]', full_body)
        for part in parts:
            part = part.strip()
            if not part: continue
            
            lower_part = part.lower()
            part_noise = any(kw in lower_part for kw in noise_keywords)
            part_app = any(kw in lower_part for kw in app_keywords)
            
            if part_app or (not part_noise):
                target_categories[category].append(part)

    # Build Markdown
    now = datetime.datetime.now().strftime('%B %d, %Y')
    release_body = f"## 📦 Release ({now})\n\n"
    
    has_content = False
    for cat, items in target_categories.items():
        if items:
            seen = set()
            unique_items = []
            for item in items:
                if item.lower() not in seen:
                    unique_items.append(item)
                    seen.add(item.lower())

            has_content = True
            release_body += f"### {cat}\n"
            for item in unique_items:
                release_body += f"- {item}\n"
            release_body += "\n"

    if not has_content:
        return f"## 📦 Release ({now})\n\nNo major application changes in this release."

    return release_body

    if not has_content:
        return f"## 📦 Release ({now})\n\nNo major application changes in this release."

    return release_body

if __name__ == "__main__":
    notes = generate_notes()
    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(notes)
    print("Release notes generated in RELEASE_NOTES.md")
