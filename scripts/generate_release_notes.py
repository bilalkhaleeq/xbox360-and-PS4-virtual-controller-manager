import subprocess
import datetime
import re
import os
import google.generativeai as genai

# --- CONFIGURATION ---
NOISE_DIRS = ['.github/', '.githooks/']
NOISE_FILES = ['README.md', 'DEVELOPER.md', 'generate_release_notes.py', '.gitignore', 'requirements.txt', 'controller_config.json']
TARGET_CATEGORIES = {
    "🚀 Features": [],
    "🐞 Bug Fixes": [],
    "🛠️ Refactors": []
}
MAPPINGS = {
    'feat': "🚀 Features",
    'fix': "🐞 Bug Fixes",
    'refactor': "🛠️ Refactors"
}
APP_KEYWORDS = ['logic', 'fix', 'bug', 'feat', 'add', 'new', 'resolv', 'prevent', 'controller', 'gamepad', 'binding', 'key', 'ps4', 'xbox', 'connection', 'driver', 'emulat', 'ui', 'gui', 'safety', 'conflict']
NOISE_KEYWORDS = ['ci', 'workflow', 'github', 'action', 'pipeline', 'devops', 'doc', 'readme', 'comment', 'manual', 'help', 'guide', 'wiki', 'build', 'package', 'dist', 'release', 'version', 'bump']

def get_last_tag():
    try:
        return subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0', 'HEAD^'], stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_app_relevant_files():
    try:
        all_files = subprocess.check_output(['git', 'ls-files']).decode().split('\n')
        app_files = []
        for f in all_files:
            if not f: continue
            is_noise = any(f.startswith(d) for d in NOISE_DIRS) or (f in NOISE_FILES)
            if not is_noise:
                app_files.append(f)
        return app_files
    except:
        return []

def get_git_diff(since_tag, files):
    if not files: return ""
    try:
        tag_ref = since_tag if since_tag else '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
        diff_cmd = ['git', 'diff', f'{tag_ref}..HEAD', '--'] + files
        return subprocess.check_output(diff_cmd).decode('utf-8', errors='ignore')
    except:
        return ""

def get_processed_commits(since_tag):
    git_cmd = ['git', 'log', f'{since_tag}..HEAD' if since_tag else 'HEAD', '--pretty=format:COMMIT:%H|%s', '--name-only']
    try:
        output = subprocess.check_output(git_cmd).decode().strip()
    except:
        return []

    processed_data = {"🚀 Features": [], "🐞 Bug Fixes": [], "🛠️ Refactors": []}
    
    # Split by "COMMIT:" but keep the marker
    raw_commits = re.split(r'\n?COMMIT:', output)
    
    for block in raw_commits:
        if not block.strip(): continue
        lines = block.strip().split('\n')
        header = lines[0]
        files = lines[1:] if len(lines) > 1 else []
        
        msg = header.split('|')[1]
        
        # Layer 1: File-Aware Relevance
        is_relevant = any(not (any(f.startswith(d) for d in NOISE_DIRS) or (f in NOISE_FILES)) for f in files)
        if not is_relevant: continue

        # Layer 2: Category & Deep-Content Filtering
        match = re.match(r'^(\w+)(\(.*\))?!?: (.*)$', msg)
        if match:
            prefix, body = match.group(1).lower(), match.group(3)
            cat = MAPPINGS.get(prefix)
            if cat:
                for part in re.split(r'[,;\n]', body):
                    part = part.strip()
                    if not part: continue
                    lower_part = part.lower()
                    if any(kw in lower_part for kw in APP_KEYWORDS) or not any(kw in lower_part for kw in NOISE_KEYWORDS):
                        processed_data[cat].append(part)
    
    return processed_data

def generate_ai_notes(diff, commit_summary, api_key):
    if not api_key or (not diff and not commit_summary): return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are a senior developer. Generate professional, high-signal release notes for the "Virtual Controller Manager".
        
        INPUT DATA:
        1. GIT DIFF (The truth of what changed):
        {diff[:15000]}
        
        2. COMMIT MESSAGES (The developer's stated intent):
        {commit_summary}
        
        RULES:
        - Use these exact categories: 🚀 Features, 🐞 Bug Fixes, 🛠️ Refactors.
        - Focus ONLY on user-facing application logic.
        - Analyze the code diffs to explain "how" things were improved (e.g., "Updated safety checks to be more lenient...").
        - Strip all mentions of CI/CD, Documentation, or internal build scripts.
        - Format as a clean Markdown list.
        - Return ONLY the categories and bullets. No intro or outro.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return None

def generate_notes():
    last_tag = get_last_tag()
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Pre-process commit data
    commits_data = get_processed_commits(last_tag)
    commit_summary = ""
    for cat, items in commits_data.items():
        if items:
            commit_summary += f"{cat}:\n" + "\n".join([f"- {i}" for i in set(items)]) + "\n"

    # Fetch code diffs for AI analysis
    app_files = get_app_relevant_files()
    diff = get_git_diff(last_tag, app_files)

    # Attempt AI synthesis
    ai_body = generate_ai_notes(diff, commit_summary, api_key)
    
    if ai_body and ("🚀" in ai_body or "###" in ai_body):
        body = ai_body
    else:
        # Robust Rule-Based Fallback (Option A style)
        body = ""
        for cat, items in commits_data.items():
            if items:
                body += f"### {cat}\n"
                for item in sorted(list(set(items))):
                    body += f"- {item}\n"
                body += "\n"

    now = datetime.datetime.now().strftime('%B %d, %Y')
    final_notes = f"## 📦 Release ({now})\n\n"
    if not body.strip():
        final_notes += "No major application changes in this release."
    else:
        final_notes += body
    
    return final_notes

if __name__ == "__main__":
    notes = generate_notes()
    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(notes)
    print("Release notes saved to RELEASE_NOTES.md")
