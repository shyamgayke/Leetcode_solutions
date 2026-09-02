import os
import requests

LEETCODE_URL = "https://leetcode.com/graphql"

session = os.environ.get("LEETCODE_SESSION")
csrf_token = os.environ.get("LEETCODE_CSRF_TOKEN")

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
        print("\nRAW LEETCODE RESPONSE:")
        print(data)
        raise RuntimeError(
            f"LeetCode GraphQL error:\n{data['errors']}"
    )

    return data["data"]


# --------------------------------------------------
# 1. Authentication
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

print("\nRecent accepted submissions:")

for item in submissions:
    print(
        f"- {item['title']} "
        f"({item['titleSlug']})"
    )


# --------------------------------------------------
# 3. Get submission list for latest problem
# --------------------------------------------------

latest = submissions[0]

print("\nTesting code retrieval:")
print(f"Problem: {latest['title']}")
print(f"Slug: {latest['titleSlug']}")

data = graphql(
    """
    query questionSubmissionList(
        $questionSlug: String!
        $offset: Int!
        $limit: Int!
    ) {
        questionSubmissionList(
            questionSlug: $questionSlug
            offset: $offset
            limit: $limit
        ) {
            submissions {
                id
                statusDisplay
                lang
                timestamp
            }
        }
    }
    """,
    {
        "questionSlug": latest["titleSlug"],
        "offset": 0,
        "limit": 10,
    },
)

result = data.get("questionSubmissionList")

if not result:
    raise RuntimeError(
        "Could not retrieve submission list."
    )

submission_list = result["submissions"]

accepted = [
    submission
    for submission in submission_list
    if submission["statusDisplay"] == "Accepted"
]

if not accepted:
    raise RuntimeError(
        "No accepted submission found."
    )

submission = accepted[0]

print("\nAccepted submission found:")
print(f"Submission ID: {submission['id']}")
print(f"Language: {submission['lang']}")
print(f"Timestamp: {submission['timestamp']}")


# --------------------------------------------------
# 4. Retrieve actual submitted code
# --------------------------------------------------

data = graphql(
    """
    query submissionDetail($submissionId: ID!) {
        submissionDetail(
            submissionId: $submissionId
        ) {
            id
            code
            lang
            statusDisplay
            runtime
            memory
        }
    }
    """,
    {
        "submissionId": submission["id"],
    },
)

details = data.get("submissionDetail")

if not details:
    raise RuntimeError(
        "Could not retrieve submission details."
    )

print("\nCODE RETRIEVED SUCCESSFULLY!")
print("--------------------------------")
print(details["code"])
print("--------------------------------")
print(f"Language: {details['lang']}")
print(f"Status: {details['statusDisplay']}")
print(f"Runtime: {details['runtime']}")
print(f"Memory: {details['memory']}")
