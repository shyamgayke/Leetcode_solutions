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
        timeout=60,
    )

    if response.status_code != 200:
        print("\nRAW HTTP RESPONSE:")
        print(response.text)
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
# 3. Process recent accepted submissions
# --------------------------------------------------

for latest in submissions:

    print("\n" + "=" * 50)
    print(f"Processing: {latest['title']}")
    print(f"Slug: {latest['titleSlug']}")

    # Get problem number
    data = graphql(
        """
        query questionInfo($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionFrontendId
            }
        }
        """,
        {
            "titleSlug": latest["titleSlug"],
        },
    )

    question = data["question"]

    problem_number = str(
        question["questionFrontendId"]
    ).zfill(4)

    folder_name = (
        f"{problem_number}-{latest['titleSlug']}"
    )

    print(f"Problem Number: {problem_number}")

    # --------------------------------------------------
    # Get submission list
    # --------------------------------------------------

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
        print("Could not retrieve submissions. Skipping.")
        continue

    submission_list = result["submissions"]

    accepted = [
        submission
        for submission in submission_list
        if submission["statusDisplay"] == "Accepted"
    ]

    if not accepted:
        print("No accepted submission found. Skipping.")
        continue

    submission = accepted[0]

    print(f"Submission ID: {submission['id']}")
    print(f"Language: {submission['lang']}")

    # --------------------------------------------------
    # Retrieve actual submitted code
    # --------------------------------------------------

    data = graphql(
        """
        query submissionDetails($submissionId: Int!) {
            submissionDetails(
                submissionId: $submissionId
            ) {
                code
            }
        }
        """,
        {
            "submissionId": int(submission["id"]),
        },
    )

    details = data.get("submissionDetails")

    if not details:
        print("Could not retrieve code. Skipping.")
        continue

    # --------------------------------------------------
    # Determine file extension
    # --------------------------------------------------

    language = submission["lang"].lower()

    extensions = {
        "cpp": "cpp",
        "c": "c",
        "python": "py",
        "python3": "py",
        "java": "java",
        "javascript": "js",
        "typescript": "ts",
        "csharp": "cs",
        "kotlin": "kt",
        "swift": "swift",
        "go": "go",
        "rust": "rs",
    }

    extension = extensions.get(language, "txt")

    # --------------------------------------------------
    # Save solution
    # --------------------------------------------------

    os.makedirs(folder_name, exist_ok=True)

    solution_file = os.path.join(
        folder_name,
        f"solution.{extension}"
    )

    with open(
        solution_file,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(details["code"])

    print(f"Saved: {solution_file}")

print("\nALL SUBMISSIONS PROCESSED SUCCESSFULLY!")

# --------------------------------------------------
# 4. Retrieve official Solution for each problem
# --------------------------------------------------

print("\nRetrieving official Solutions...")

for latest in submissions:

    title = latest["title"]
    slug = latest["titleSlug"]

    # Get problem number
    data = graphql(
        """
        query questionInfo($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionFrontendId
            }
        }
        """,
        {
            "titleSlug": slug,
        },
    )

    question = data["question"]

    problem_number = str(
        question["questionFrontendId"]
    ).zfill(4)

    solution_folder = (
        f"{problem_number}-{slug}"
    )

    print(f"\nProcessing Solution: {title}")

    # Retrieve official solution
    data = graphql(
        """
        query officialSolution($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                solution {
                    id
                    canSeeDetail
                    content
                }
            }
        }
        """,
        {
            "titleSlug": slug,
        },
    )

    question_solution = (
        data["question"].get("solution")
    )

    if not question_solution:
        print("No official solution available.")
        continue

    content = question_solution.get("content")

    if not content:
        print("Solution exists, but no content was returned.")
        continue

    readme_file = os.path.join(
        solution_folder,
        "README.md"
    )

    readme_content = f"""# {title}

## Official Solution

{content}
"""

    with open(
        readme_file,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(readme_content)

    print(f"Saved: {readme_file}")

print("\nALL SOLUTIONS PROCESSED SUCCESSFULLY!")



   # --------------------------------------------------
# 5. Inspect personal Solution Article structure
# --------------------------------------------------

print("\nTesting personal Solution Article structure...")

data = graphql(
    """
    query ugcArticleSolutionArticles(
        $questionSlug: String!
    ) {
        ugcArticleSolutionArticles(
            questionSlug: $questionSlug
        ) {
            edges {
                node {
                    title
                    slug
                }
            }
        }
    }
    """,
    {
        "questionSlug": "longest-common-prefix"
    }
)

print("\nPersonal Solution Articles:")

for edge in data["ugcArticleSolutionArticles"]["edges"]:
    article = edge["node"]

    print("\n-----------------------------")
    print(f"Title: {article.get('title')}")
    print(f"Slug: {article.get('slug')}")
