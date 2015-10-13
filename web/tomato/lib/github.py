__author__ = 't-gerhard'

import github3  # https://github.com/sigmavirus24/github3.py
from ..settings import github_access_token, github_repository_owner, github_repository_name
from .error import Error

class GithubError(Error):
	TYPE="github"
	NOT_CONFIGURED = "not configured"

def is_enabled():
	if not github_access_token:
		return False
	return True

def connect():
	if not is_enabled():
		raise GithubError(type=GithubError.NOT_CONFIGURED, message="GitHub Access Token is not set in webfrontend settings")
	return github3.login(token=github_access_token)


def create_issue(title, body):
	gh = connect()
	repo = gh.repository(github_repository_owner, github_repository_name)
	issue = repo.create_issue(title, body)
	return issue
