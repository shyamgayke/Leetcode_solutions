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

# --------------------------------------------------
# 1. Check authentication
# --------------------------------------------------

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

username = user_status["username"]

print(f"Logged in as: {username}")


# --------------------------------------------------
# 2. Get recent accepted submissions
# --------------------------------------------------

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
    "limit": 5,
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

submissions = data["data"]["recentAcSubmissionList"]

if not submissions:
    raise RuntimeError("No accepted submissions found.")

print(f"Found {len(submissions)} recent accepted submissions.")

for submission in submissions:
    print(
        f"- {submission['title']} "
        f"({submission['titleSlug']})"
    )


# --------------------------------------------------
# 3. Get details of the most recent submission
# --------------------------------------------------

latest = submissions[0]

print("\nTesting submission:")
print(f"Problem: {latest['title']}")
print(f"Slug: {latest['titleSlug']}")


query = """
query submissionList(
    $username: String!
    $slug: String!
) {
    submissionList(
        username: $username
        questionSlug: $slug
        limit: 1
    ) {
        submissions {
            id
            lang
            statusDisplay
        }
    }
}
"""

variables = {
    "username": username,
    "slug": latest["titleSlug"],
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

submission_data = (
    data.get("data", {})
    .get("submissionList", {})
    .get("submissions", [])
)

if not submission_data:
    raise RuntimeError(
        "Could not retrieve submission details."
    )

submission = submission_data[0]

print("\nSubmission details:")
print(f"Submission ID: {submission['id']}")
print(f"Language: {submission['lang']}")
print(f"Status: {submission['statusDisplay']}")
