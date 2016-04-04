__author__ = 't-gerhard'

import github3  # https://github.com/sigmavirus24/github3.py

from settings import get_settings, Config
from .. import settings as config_module
settings = get_settings(config_module)

from .error import Error

class GithubError(Error):
	TYPE = "github"
	NOT_CONFIGURED = "not configured"

def is_enabled():
	config = settings.get_github_settings()
	if not config[Config.GITHUB_ACCESS_TOKEN]:
		return False
	return True

def connect(access_token):
	if not is_enabled():
		raise GithubError(type=GithubError.NOT_CONFIGURED, message="GitHub Access Token is not set in webfrontend settings")
	return github3.login(token=access_token)


def create_issue(title, body):
	config = settings.get_github_settings()
	gh = connect(config[Config.GITHUB_ACCESS_TOKEN])
	repo = gh.repository(config[Config.GITHUB_REPOSITORY_OWNER], config[Config.GITHUB_REPOSITORY_NAME])
	issue = repo.create_issue(title, body)
	return issue
