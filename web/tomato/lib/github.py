__author__ = 't-gerhard'

import github3

class config:
	github_access_token = "6f07fa7f0f0de0c9c211672ad875863782996e19"
	repository_owner = "t-gerhard"
	repository_name = "ToMaTo"

def connect():
	token = config.github_access_token
	return github3.login(token=token)


def create_issue(title, body):
	gh = connect()
	repo = gh.repository(config.repository_owner, config.repository_name)
	issue = repo.create_issue(title, body)
	return issue
