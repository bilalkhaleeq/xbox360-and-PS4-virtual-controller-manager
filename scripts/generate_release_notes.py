import subprocess
import datetime
import re
import os
from google import genai

# --- CONFIGURATION ---
NOISE_DIRS = ['.github/', '.githooks/', 'scripts/', '__pycache__/', 'build/', 'dist/']
NOISE_FILES = ['README.md', 'DEVELOPER.md', '.gitignore', 'requirements.txt', 'controller_config.json', 'virtual_controller.spec']
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
        # We look for the latest tag reachable from the parent of the current commit.
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

    processed_data = {"🚀 Features": [], "🐞 Bug Fixes": [], "🛠️ Refactors": [], "📦 Other Updates": []}
    raw_commits = re.split(r'\n?COMMIT:', output)
    
    for block in raw_commits:
        if not block.strip(): continue
        lines = block.strip().split('\n')
        header = lines[0]
        files = lines[1:] if len(lines) > 1 else []
        msg = header.split('|')[1]
        
        match = re.match(r'^(\w+)(\(.*\))?!?: (.*)$', msg)
        is_app_relevant = any(not (any(f.startswith(d) for d in NOISE_DIRS) or (f in NOISE_FILES)) for f in files)

        if match:
            prefix, body = match.group(1).lower(), match.group(3)
            cat = MAPPINGS.get(prefix)
            if (prefix in ['feat', 'fix']) or (cat and is_app_relevant):
                for part in re.split(r'[,;\n]', body):
                    part = part.strip()
                    if not part: continue
                    lower_part = part.lower()
                    if any(kw in lower_part for kw in APP_KEYWORDS) or not any(kw in lower_part for kw in NOISE_KEYWORDS):
                        processed_data[cat].append(part)
        elif is_app_relevant:
            processed_data["📦 Other Updates"].append(msg)
    
    return processed_data

import time

def generate_ai_notes(diff, commit_summary, api_key):
    if not api_key:
        print("[INFO] No GEMINI_API_KEY found. Skipping AI generation.")
        return None
    if not diff and not commit_summary:
        print("[INFO] No changes found to summarize. Skipping AI.")
        return None
        
    # Attempt with Retry logic for transient errors
    for attempt in range(2):
        try:
            if attempt > 0:
                print(f"[INFO] Retrying AI synthesis (Attempt {attempt + 1})...")
                time.sleep(10) # Longer wait for quota reset

            print("[INFO] Contacting Google Gemini API for synthesis...")
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are a senior product manager. Generate professional, user-friendly release notes for the "Virtual Controller Manager".
            
            INPUT DATA:
            1. GIT DIFF (Technical changes):
            {diff[:5000]}
            
            2. COMMIT MESSAGES (Developer intent):
            {commit_summary}
            
            STRICT RULES FOR CONTENT:
            - Use ONLY simple, non-technical language that a regular gamer/user would understand.
            - NEVER mention code terms, method names (e.g., no 'check_local_binding'), or technical jargon (e.g., no 'instantiated', 'decoupled', 'architecture').
            - Focus on the practical BENEFIT to the user (e.g., "You can now do X" or "Fixed a crash when Y").
            - Categories: 🚀 Features, 🐞 Bug Fixes, 🛠️ Improvements (Use 'Improvements' instead of 'Refactors' for users).
            - Format: Return ONLY the categories and bullet points. No intro or outro.
            """
            # Use gemini-flash-latest as discovered in list_models
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            if ("429" in str(e) or "404" in str(e)) and attempt == 0:
                print(f"[WARNING] API encountered an issue ({e}). Waiting to retry...")
                continue
            print(f"[ERROR] Gemini API call failed: {e}")
            break
    return None

def generate_notes():
    last_tag = get_last_tag()
    api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"[INFO] Analyzing repository state since: {last_tag if last_tag else 'beginning'}")
    
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
        print("[SUCCESS] Release notes synthesized by Gemini 2.0.")
        body = ai_body
    else:
        print("[INFO] Falling back to rule-based filtering logic.")
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
    print("[INFO] Final release notes written to RELEASE_NOTES.md")
