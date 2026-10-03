import pytest
from services.github_service import validate_github_username
from routers.resume import normalize_github_url
from fastapi import HTTPException


def test_validate_github_username_valid():
    assert validate_github_username("torvalds") == "torvalds"
    assert validate_github_username("octocat-123") == "octocat-123"
    assert validate_github_username("a-b-c") == "a-b-c"
    assert validate_github_username("User123") == "User123"


def test_validate_github_username_invalid():
    invalid_cases = [
        "../../user",
        "a/b",
        "user name",
        "-starts-with-dash",
        "has$pecial",
        "a" * 40,  # exceeds 39 chars
        "",
        None,
    ]
    for case in invalid_cases:
        with pytest.raises(ValueError):
            validate_github_username(case)


def test_normalize_github_url_rejects_malicious_usernames():
    with pytest.raises(HTTPException) as exc_info:
        normalize_github_url("https://github.com/../../malicious")
    assert exc_info.value.status_code == 422

    with pytest.raises(HTTPException) as exc_info:
        normalize_github_url("https://github.com/invalid/user")
    assert exc_info.value.status_code == 422
