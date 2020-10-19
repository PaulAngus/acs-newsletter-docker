#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Usage:
  fixed_issues.py [--config=<config.json>]
                  [-t <arg> | --gh_token=<arg>] 
                  [-c <arg> | --prev_rel_commit=<arg>]
                  [-b <arg> | --branch=<arg>]  
                  [--repo=<arg>] 
                  [--gh_base_url=<arg>] 
                  [--jira_base_url=<arg>]
                  [--jira_server_url=<arg>]
                  [--col_branch_width=<arg>] 
                  [--col_github_width=<arg>]
                  [--col_jira_width=<arg>]
                  [--col_type_width=<arg>] 
                  [--col_priority_width=<arg>]
                  [--col_desc_width=<arg>]
  fixed_issues.py (-h | --help)
Options:
  -h --help                         Show this screen.
  --config=<config.json>            Path to a JSON config file with an object of config options.
  -t <arg> --gh_token=<arg>         Required: Your Github token from https://github.com/settings/tokens 
                                      with `repo/public_repo` permissions.
  -c <arg> --prev_rel_commit=<arg>  Required: The commit hash of the previous release.
  -b <arg> --branches=<arg>         Required: Comma separated list of branches to report on (eg: 4.7,4.8,4.9).
                                      The last one is assumed to be `master`, so `4.7,4.8,4.9` would
                                      actually be represented by 4.7, 4.8 and master.
  --repo=<arg>                      The name of the repo to use [default: apache/cloudstack].
  --gh_base_url=<arg>               The base Github URL for pull requests 
                                      [default: https://github.com/apache/cloudstack/pull/].
  --jira_base_url=<arg>             The base Jira URL for issues
                                      [default: https://issues.apache.org/jira/browse/].
  --jira_server_url=<arg>           The Jira server URL [default: https://issues.apache.org/jira].
  --col_branch_width=<arg>          The width of the Branches column [default: 25].
  --col_github_width=<arg>          The width of the Github PR column [default: 10].
  --col_jira_width=<arg>            The width of the Jira Issue column [default: 20].
  --col_type_width=<arg>            The width of the Issue Type column [default: 15].
  --col_priority_width=<arg>        The width of the Issue Priority column [default: 10].
  --col_desc_width=<arg>            The width of the Description column [default: 60].
  
Sample json file contents:

{
	"--gh_token":"******************",
	"--prev_release_commit":"",
	"--repo_name":"apache/cloudstack",
	"--branch":"4.11",
	"--prev_release_ver":"4.11.1.0",
	"--new_release_ver":"4.11.2.0"
}


"""

import docopt
import json
from github import Github
from prettytable import PrettyTable
import itertools
import os.path
import time

import pprint
import re
import sys

def load_config():
    """
    Parse the command line arguments and load in the optional config file values
    """
    args = docopt.docopt(__doc__)
    if args['--config'] and os.path.isfile(args['--config']):
        json_args = {}
        try:
            with open(args['--config']) as json_file:    
                json_args = json.load(json_file)
        except Exception as e:
            print(("Failed to load config file '%s'" % args['--config']))
            print(("ERROR: %s" % str(e)))
        if json_args:
            args = merge(args, json_args)
#     since we are here, check that the required fields exist
    valid_input = True
    for arg in ['--gh_token', '--prev_release_ver', '--branch', '--repo', '--new_release_ver']:
        if not args[arg] or (isinstance(args[arg], list) and not args[arg][0]):
            print(("ERROR: %s is required" % arg))
            valid_input = False
    if not valid_input:
        sys.exit(__doc__)
    return args

def merge(primary, secondary):
    """
    Merge two dictionaries.
    Values that evaluate to true take priority over false values.
    `primary` takes priority over `secondary`.
    """
    return dict((str(key), primary.get(key) or secondary.get(key))
                for key in set(secondary) | set(primary))

# run the code...
if __name__ == '__main__':
    args = load_config()
#     repository details
    gh_token = args['--gh_token']
    gh = Github(gh_token)
    repo_name = args['--repo']
    prev_release_ver = args['--prev_release_ver']
    prev_release_commit = args['--prev_release_commit']
    new_release_ver = args['--new_release_ver']
    branch = args['--branch']

    gh_base_url = args['--gh_base_url']

#   table column widths
    branch_len = int(args['--col_branch_width'])
    gh_len = int(args['--col_github_width'])
    issue_type_len = int(args['--col_type_width'])
    issue_priority_len = int(args['--col_priority_width'])
    desc_len = int(args['--col_desc_width'])

    merged_features_file = str(os.path.splitext(args['--config'])[0])+"-features.rst"
    merged_fixes_file = str(os.path.splitext(args['--config'])[0])+"-fixes.rst"

    repo = gh.get_repo(repo_name)

    ## TODO - get commit -> commit date from tag on master.
    ## Searching seems a waste
    ## and gets API overuse failures

    #repo_tags = repo.get_tags()

    if prev_release_commit:
        print("Previous Release Commit SHA found, skipping pre_release_ver search")
        prev_release_sha = prev_release_commit
    else:
        print("Finding commit SHA for previous version " + prev_release_ver)
        for tag in repo_tags:
            if tag.name == prev_release_ver:
                prev_release_sha = tag.commit.sha
                #print(prev_release_sha)
    commit = repo.get_commit(sha=prev_release_sha)
    prev_release_commit_date=str(commit.commit.author.date.date())    #break

    if not commit:
        print("No starting point found via version tag or commit SHA")
        exit

    print("Enumerating closed and merged PRs in master")
    merged_features = {}
    merged_fixes = {}

    print("Retrieving Pull Request Issues from Github")
    search_string = f"repo:apache/cloudstack is:closed is:pr is:merged merged:>={prev_release_commit_date}"
    issues = gh.search_issues(search_string)
    fixes_table = PrettyTable(["PR Number", "Title", "Priority", "blank"]) 
    features_table = PrettyTable(["PR Number", "Title", "Priority", "blank"])
    dontknow_table = PrettyTable(["PR Number", "Title", "Priority", "blank"])

    print("Processing Pull Request Issues")
    for issue in issues:
        pr = issue.repository.get_pull(issue.number)
        label = []
        pr_num = str(pr.number)
        print("Found PR: " + pr_num)
        labels = pr.labels
        if [l.name for l in labels if l.name=='type:new-feature' or l.name=='type:enhancement']:
            features_table.add_row([pr_num, pr.title.strip(), "-", "-"]) 
            print("--- PR: " + pr_num + "--- feature label")
        if [l.name for l in labels if l.name=='type:bug' or l.name=='BUG']:
            fixes_table.add_row([pr_num, pr.title.strip(), "-", "-"]) 
            print("--- PR: " + pr_num + "--- fix label")
        else:
            print("Labels not matched")
            dontknow_table.add_row([pr_num, pr.title.strip(), "-", "-"]) 

    print("writing tables")
    fixes_table_txt = fixes_table.get_string()
    with open('%s.txt' % merged_fixes_file ,"w") as file:
        file.write(fixes_table_txt)
        file.write('\n%s Issues listed\n\n' % str(len(merged_fixes)))
    file.close()
    print(("Commit data output to %s" % merged_fixes_file))

    features_table_txt = features_table.get_string()
    with open('%s.txt' % merged_features_file ,"w") as file:
        file.write(features_table_txt)
        file.write('\n%s Issues listed\n\n' % str(len(merged_features)))
    file.close()
    print(("Commit data output to %s" % merged_features_file))

#    file = open('%s.txt' % merged_features_file ,"w")
#    file.write('print(dontknow_table)')
#    file.write('\n%s Issues listed\n\n' % str(len(merged_features)))
#    file.close()
#    print(("Commit data output to %s" % merged_features_file))

# output the links we referenced earlier
#    for link in links:
#        file.write('%s \n' % link)
#        file.write('')