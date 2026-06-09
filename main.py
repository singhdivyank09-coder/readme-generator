import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GITHUB_URL = "https://api.github.com"


def get_github_profile(username):
    r = requests.get(f"{GITHUB_URL}/users/{username}", timeout=10)
    if r.status_code == 404:
        print("User not found.")
        return None
    return r.json()


def get_github_repos(username):
    r = requests.get(f"{GITHUB_URL}/users/{username}/repos?per_page=100&sort=updated", timeout=10)
    return r.json()


def get_repo_details(username, repo_name):
    r = requests.get(f"{GITHUB_URL}/repos/{username}/{repo_name}", timeout=10)
    return r.json()


def get_user_inputs():
    print("\n--- Tell me more about your project ---")
    description  = input("What does your project do? (1-2 lines): ").strip()
    tech_stack   = input("Tech stack (e.g. React, Node.js, MongoDB): ").strip()
    features     = input("Key features (comma separated): ").strip()
    installation = input("How to install/run it? (e.g. npm install && npm start): ").strip()
    usage        = input("How to use it? (brief): ").strip()
    license      = input("License (e.g. MIT, Apache, None): ").strip() or "MIT"
    screenshots  = input("Do you have a screenshots folder? (y/n): ").strip().lower()

    return {
        "description": description,
        "tech_stack": tech_stack,
        "features": features,
        "installation": installation,
        "usage": usage,
        "license": license,
        "has_screenshots": screenshots == "y"
    }


def generate_readme(repo_data, profile_data, user_inputs):
    screenshots_section = """
## 📸 Screenshots

| Screenshot | Description |
| --- | --- |
| <img src="screenshots/home.png" width="300"> | Home page |
| <img src="screenshots/dashboard.png" width="300"> | Dashboard |
""" if user_inputs["has_screenshots"] else ""

    author_name = profile_data.get('name') or profile_data.get('login', 'Unknown')
    repo_name   = repo_data.get('name', 'N/A')
    github_url  = profile_data.get('html_url', 'N/A')

    prompt = f"""
You are a professional technical writer. Generate a stunning, complete GitHub README.md.

Developer Info:
- Name: {author_name}
- Bio: {profile_data.get('bio', 'N/A')}
- GitHub: {github_url}

Repository Info:
- Repo Name: {repo_name}
- GitHub Description: {repo_data.get('description', 'N/A')}
- Primary Language: {repo_data.get('language', 'N/A')}
- Stars: {repo_data.get('stargazers_count', 0)}
- Forks: {repo_data.get('forks_count', 0)}
- Topics: {', '.join(repo_data.get('topics', [])) or 'None'}
- Repo URL: {repo_data.get('html_url', 'N/A')}

User Provided Details:
- What it does: {user_inputs['description']}
- Tech Stack: {user_inputs['tech_stack']}
- Key Features: {user_inputs['features']}
- Installation: {user_inputs['installation']}
- Usage: {user_inputs['usage']}
- License: {user_inputs['license']}

Generate the README.md following these STRICT rules:

RULE 1 - TITLE: Start with # (H1) not bold. Example: # 💡 {repo_name}
RULE 2 - BADGES: Use shields.io badges for stars, forks, language, license. All must be on separate lines.
RULE 3 - TAGLINE: One catchy italic line after badges. Example: *"Your tagline here"*
RULE 4 - TABLE OF CONTENTS: Use proper markdown anchor links.
RULE 5 - ABOUT: 3-4 sentences, engaging, specific to the project. No generic filler.
RULE 6 - FEATURES: Use checkboxes with emojis. At least 6 features. Example: - [x] 🔐 User authentication
RULE 7 - TECH STACK: Table with 3 columns — Technology, Version, Purpose.
RULE 8 - GETTING STARTED: Prerequisites as a bullet list. Installation as numbered steps.
RULE 9 - FOLDER STRUCTURE: Use a proper code block with tree structure.
RULE 10 - CONTRIBUTING: At least 5 steps — fork, clone, branch, commit, pull request.
RULE 11 - AUTHOR: Must include the author's actual name ({author_name}), GitHub link ({github_url}), and a warm thank you message.
RULE 12 - NO PLACEHOLDERS: Every section must be filled with real specific content based on the project info provided.

{screenshots_section}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }

    r = requests.post(GROQ_URL, headers=headers, json=body, timeout=30)
    data = r.json()
    return data["choices"][0]["message"]["content"]


def save_readme(content, repo_name):
    filename = f"{repo_name}_README.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ README saved as: {filename}")


def main():
    username = input("Enter GitHub username: ").strip()

    profile = get_github_profile(username)
    if not profile:
        return

    print(f"\nHello, {profile.get('name', username)}!")
    print(f"Public Repos: {profile.get('public_repos', 0)}\n")

    repos = get_github_repos(username)

    print("Your repositories:")
    for i, repo in enumerate(repos, start=1):
        print(f"  {i}. {repo['name']} ({repo.get('language', 'N/A')})")

    choice = int(input("\nEnter repo number to generate README for: ")) - 1
    selected_repo = repos[choice]['name']

    print(f"\nFetching details for: {selected_repo}...")
    repo_data = get_repo_details(username, selected_repo)

    user_inputs = get_user_inputs()

    print("\n⏳ Generating README with AI...")
    readme_content = generate_readme(repo_data, profile, user_inputs)

    save_readme(readme_content, selected_repo)

    print("\n--- PREVIEW (first 800 chars) ---\n")
    print(readme_content[:800] + "\n...")


if __name__ == "__main__":
    main()