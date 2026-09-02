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


def graphql(query, variables=None):
    response = requests.post(
        LEETCODE_URL,
        json={
            "query": query,
            "variables": variables or {},
        },
        headers=headers,
        cookies=cookies,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(
            f"LeetCode GraphQL error:\n{data['errors']}"
        )

    return data["data"]


# --------------------------------------------------
# 1. Check authentication
# --------------------------------------------------

data = graphql("""
query {
    userStatus {
        isSignedIn
        username
    }
}
""")

user_status = data["userStatus"]

if not user_status["isSignedIn"]:
    raise RuntimeError("LeetCode authentication failed.")

username = user_status["username"]

print(f"Logged in as: {username}")


# --------------------------------------------------
# 2. Get recent accepted submissions
# --------------------------------------------------

data = graphql(
    """
    query recentAcSubmissions(
        $username: String!
        $limit: Int!
    ) {
        recentAcSubmissionList(
            username: $username
            limit: $limit
        ) {
            title
            titleSlug
            timestamp
        }
    }
    """,
    {
        "username": username,
        "limit": 5,
    },
)

submissions = data["recentAcSubmissionList"]

if not submissions:
    raise RuntimeError("No accepted submissions found.")

print(
    f"Found {len(submissions)} recent accepted submissions."
)

for item in submissions:
    print(
        f"- {item['title']} "
        f"({item['titleSlug']})"
    )


# --------------------------------------------------
# 3. Test retrieving submission details
# --------------------------------------------------

latest = submissions[0]

print("\nTesting submission:")
print(f"Problem: {latest['title']}")
print(f"Slug: {latest['titleSlug']}")


data = graphql(
    """
    query submissionDetails(
        $titleSlug: String!
    ) {
        question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            difficulty
        }
    }
    """,
    {
        "titleSlug": latest["titleSlug"],
    },
)

question = data.get("question")

if not question:
    raise RuntimeError(
        "Could not retrieve problem information."
    )

print("\nProblem details:")
print(f"Question ID: {question['questionId']}")
print(
    f"Problem Number: "
    f"{question['questionFrontendId']}"
)
print(f"Title: {question['title']}")
print(f"Difficulty: {question['difficulty']}")

print("\nSUCCESS: Problem information retrieved.")
