import os
import requests

LEETCODE_URL = "https://leetcode.com/graphql"

session = os.environ.get("LEETCODE_SESSION")
csrf_token = os.environ.get("LEETCODE_CSRF_TOKEN")

if not session or not csrf_token:
    raise RuntimeError("LeetCode credentials are missing.")

cookies = {
    "LEETCODE_SESSION": session,
    "csrftoken": csrf_token,
}

headers = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0",
}

query = """
query {
    userStatus {
        isSignedIn
        username
    }
}
"""

response = requests.post(
    LEETCODE_URL,
    json={"query": query},
    headers=headers,
    cookies=cookies,
    timeout=30,
)

response.raise_for_status()

data = response.json()

user_status = data.get("data", {}).get("userStatus", {})

if not user_status.get("isSignedIn"):
    raise RuntimeError("LeetCode authentication failed.")

username = user_status.get("username")

print(f"Logged in as: {username}")

query = """
query recentAcSubmissions($username: String!, $limit: Int!) {
    recentAcSubmissionList(username: $username, limit: $limit) {
        title
        titleSlug
        timestamp
    }
}
"""

variables = {
    "username": username,
    "limit": 20,
}

response = requests.post(
    LEETCODE_URL,
    json={
        "query": query,
        "variables": variables,
    },
    headers=headers,
    cookies=cookies,
    timeout=30,
)

response.raise_for_status()

data = response.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

submissions = data.get("data", {}).get(
    "recentAcSubmissionList", []
)

print(f"Found {len(submissions)} recent accepted submissions.")

for submission in submissions:
    print(
        f"- {submission['title']} "
        f"({submission['titleSlug']})"
    )
