#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Preparing to run it:
#   brew install pipenv   # or other installation method
#   pipenv install
#   generate a personal access token at https://github.com/settings/tokens

# Running it:
#   GITHUB_TOKEN=xxxxxx pipenv run python add-metadata.py < README.md > README-NEW.md
# Check README-NEW.md, if it is ok run:
#   mv README-NEW.md README.md  

import fileinput
import os
import re
import sys

from datetime import datetime, timedelta
from github import Github

g = Github(os.environ['GITHUB_TOKEN'])

# gh_repo_regex = re.compile('\[([\w\._-]+\/[\w\._-]+)\]\(@ghRepo\)')
gh_repo_regex = re.compile('\[(.*)\]\(https:\/\/github.com\/([\w\._-]+\/[\w\._-]+)\) \- (.*)')

first_regex = re.compile('\[(.*)\]\((.*)\)(.*)')
second_regex = re.compile('(https|http):\/\/github.com\/([\w\._-]+\/[\w\._-]+)')

prevLineEmpty = False
header = 'Name | Description | GitHub Activity\n---- | ----------- | ---------------\n'


def github_table_row(repo):
    name = repo.name
    if repo.stargazers_count >= 500:
        name = f"**{name}**"

    project_link = f"[{name}]({repo.html_url})"
    stars_shield = f"![GitHub stars](https://img.shields.io/github/stars/{repo.full_name})"
    commit_shield = f"![GitHub commit activity](https://img.shields.io/github/commit-activity/y/{repo.full_name})"

    return f"{project_link} | {repo.description} | {stars_shield} {commit_shield}"


def warn(msg):
    print(f"Warn: {msg}", file=sys.stderr)


def retrieve_repo(name):
    try:
        repo = g.get_repo(name)
    except Exception:
        warn(f"Error occured while getting {name} repo")
        raise
    print('.', file=sys.stderr, end='', flush=True)
    # check_freshness(repo)
    return repo


def check_freshness(repo):
    if repo.archived:
        warn(f"Repo {repo.full_name} is archived")
    elif repo.pushed_at < datetime.utcnow() - timedelta(days=180):
        warn(f"Repo {repo.full_name} has not been pushed to since {repo.pushed_at}")


def parse(line):
    global prevLineEmpty
    first = first_regex.search(line)
    if first:
        res = ''
        name = first.group(1)
        url = first.group(2)
        description = first.group(3)
        project_link = f"[{name}]({url})"

        if len(url) > 0 and url[0] == '#':
            return line.rstrip()

        second = second_regex.search(url)
        if second:
            repo_name = second.group(2)
            try:
                res = github_table_row(retrieve_repo(repo_name))
            except Exception:
                warn(f"Error occured while getting {repo_name} repo")
                res = f"{project_link} | {description} | **FAILED** "
        else:
            res = f"{project_link} | {description} | "
        if prevLineEmpty:
            prevLineEmpty = False
            return header + res
        else:
            return res


    else:
        if line == '\n':
            prevLineEmpty = True
        else:
            prevLineEmpty = False
        return line.rstrip()



def run():
    for line in fileinput.input():
        print(parse(line))


run()
