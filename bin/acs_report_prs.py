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
                  [--col_title_width=<arg>] 

  fixed_issues.py (-h | --help)
Options:
  -h --help                         Show this screen.
  --config=<config.json>            Path to a JSON config file with an object of config options.
  --gh_token=<arg>         Required: Your Github token from https://github.com/settings/tokens 
                                      with `repo/public_repo` permissions.
  --prev_rel_commit=<arg>  Required: The commit hash of the previous release.
  --branches=<arg>         Required: Comma separated list of branches to report on (eg: 4.7,4.8,4.9).
  --new_release_ver=<arg            not used in this iteration yet

                                      The last one is assumed to be `master`, so `4.7,4.8,4.9` would
                                      actually be represented by 4.7, 4.8 and master.
  --repo=<arg>                      The name of the repo to use [default: apache/cloudstack].
  --gh_base_url=<arg>               The base Github URL for pull requests 
                                      [default: https://github.com/apache/cloudstack/pull/].
  --col_title_width=<arg>          The width of the title column [default: 60].
  --docker_created_config=<arg>     used to know whether to remove conf file if in container (for some safety)    

Sample json file contents:

{
	"--gh_token":"******************",
	"--prev_release_commit":"",
	"--repo_name":"apache/cloudstack",
	"--branch":"4.11",
	"--prev_release_ver":"4.11.1.0",
	"--new_release_ver":"4.11.2.0"
}

requires: python3.8 + docopt pygithub prettytable gitpython

"""

from typing import DefaultDict
import docopt
import json
from github import Github
from prettytable import PrettyTable
import os.path
from os import path
import re
import sys
import subprocess
from  datetime import datetime, timedelta
import subprocess
import shutil
import pygit2
from lib import processors


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
    print('\nInitialising...\n\n')

    args = load_config()
#   repository details
    gh_token = args['--gh_token']
    gh = Github(gh_token)
    repo_name = args['--repo']
    prev_release_ver = args['--prev_release_ver']
    prev_release_commit_sha = args['--prev_release_commit_sha']
    new_release_ver = args['--new_release_ver']
    branch = args['--branch']
    tmp_dir = args['--tmp_dir']
    gh_base_url = args['--gh_base_url']

    # default column width to 60
    if 'col_title_width' in locals():
        col_title_width = int(args['--col_title_width'])
    else:
        col_title_width = 60
    
    # Delete config file if was dynaicall 
    if 'docker_created_config' in locals():
        docker_created_config = bool(args('--docker_created_config'))
    else:
        docker_created_config = bool(False)

    if docker_created_config:
        if args['--config'] and os.path.isfile(args['--config']):
            os.remove("demofile.txt")

    prs_file = "prs.rst"
    tmp_repo_dir = tmp_dir + "/repo"
    wip_features_table = PrettyTable(["PR Number", "Title", "Type", "Note"])
    fixes_table = PrettyTable(["PR Number", "Title", "Type", "Note"]) 
    features_table = PrettyTable(["PR Number", "Title", "Type", "Note"])
    dontknow_table = PrettyTable(["PR Number", "Title", "Type", "Note"])
    old_pr_table = PrettyTable(["PR Number", "Title", "Type", "Note"])
    old_pr_table.align["Title"] = "l"
    wip_features_table.align["Title"] = "l"
    features_table.align["Title"] = "l"
    fixes_table.align["Title"] = "l"
    dontknow_table.align["Title"] = "l"
    old_pr_table._max_width = {"Title":col_title_width}
    wip_features_table._max_width = {"Title":col_title_width}
    features_table._max_width = {"Title":col_title_width}
    fixes_table._max_width = {"Title":col_title_width}
    dontknow_table._max_width = {"Title":col_title_width}

    repo = gh.get_repo(repo_name)

    ## TODO - get commit -> commit date from tag on master.
    ## Searching seems a waste

    #repo_tags = repo.get_tags()

    if prev_release_commit_sha:
        print("Previous Release Commit SHA found in conf file, skipping pre release SHA search.\n")
        prev_release_sha = prev_release_commit_sha
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


    print("Enumerating Open WIP PRs in master\n")
    print("- Retrieving Pull Request Issues from Github")
    search_string = f"repo:apache/cloudstack is:open is:pr label:wip"
    issues = gh.search_issues(search_string)
    wip_features = 0
    old_prs = 0

    print("- Processing OPEN Pull Requests (as issues)\n")
    for issue in issues:
        pr = issue.repository.get_pull(issue.number)
        label = []
        pr_num = str(pr.number)
        labels = pr.labels
        if [l.name for l in labels if l.name=='wip']:
            wip_features_table.add_row([pr_num, pr.title.strip(), "-", "-"]) 
            print("-- Found open PR : " + pr_num + " with WIP label")
            wip_features += 1

        creation_date = pr.created_at
        check_date_old = datetime.now() - timedelta(days=365)
        check_date_very_old = datetime.now() - timedelta(days=2*365)
        if creation_date < check_date_very_old:
            print("**** More than 2 years old")
            old_prs += 1
            old_pr_table.add_row([pr_num, pr.title.strip(), "Very old PR", "Add label age:2years_plus"])

        elif creation_date < check_date_old:
            print("**** More than 1 year old")
            old_prs += 1
            old_pr_table.add_row([pr_num, pr.title.strip(), "Old PR", "Add label age:1year_plus"])
            

    print("\nEnumerating closed and merged PRs in master\n")

    print("- Retrieving Pull Request Issues from Github")
    search_string = f"repo:apache/cloudstack is:closed is:pr is:merged merged:>={prev_release_commit_date}"
    issues = gh.search_issues(search_string)
    features = 0
    fixes = 0
    uncategorised = 0

    print("\nFinding reverted PRs")
    reverted_shas = processors.get_reverted_commits(repo, branch,prev_release_commit_date, tmp_repo_dir)
    print("- Found these reverted commits:\n", reverted_shas)

    print("\nProcessing MERGED Pull Request Issues\n")
    for issue in issues:
        label_matches = 0
        pr = issue.repository.get_pull(issue.number)
        pr_commit_sha = pr.merge_commit_sha
        if pr_commit_sha in reverted_shas:
            print("- Skipping PR %s, its been reverted", pr.merge_commit_sha)
        else:
            label = []
            pr_num = str(pr.number)
            labels = pr.labels
            if [l.name for l in labels if l.name=='type:new-feature']:
                features_table.add_row([pr_num, pr.title.strip(), "New Feature", "-"]) 
                print("-- Found PR: " + pr_num + " with feature label")
                features += 1
                label_matches += 1
            if [l.name for l in labels if l.name=='type:enhancement']:
                features_table.add_row([pr_num, pr.title.strip(), "Enhancement", "-"]) 
                print("-- Found PR: " + pr_num + " with enhancement label")
                features += 1
                label_matches += 1
            if [l.name for l in labels if l.name == 'type:bug' or l.name == 'BUG' or l.name == 'type:cleanup']:
                fixes_table.add_row([pr_num, pr.title.strip(), "Bug Fix", "-"]) 
                print("-- Found PR: " + pr_num + " with fix label")
                fixes += 1
                label_matches += 1
            if label_matches == 0:
                print("-- Found PR: " + pr_num + " with no matching label")
                dontknow_table.add_row([pr_num, pr.title.strip(), "-", "-"])
                uncategorised += 1

    print("\nwriting tables")
    wip_features_table_txt = wip_features_table.get_string()
    fixes_table_txt = fixes_table.get_string()
    features_table_txt = features_table.get_string()
    dontknow_table_txt = dontknow_table.get_string()
    old_pr_txt = old_pr_table.get_string()
    with open(prs_file ,"w") as file:
        file.write('\nWork in Progress PRs\n\n')
        file.write(wip_features_table_txt)
        file.write('\n%s PRs listed\n\n' % str(wip_features))
        file.write('New (merged) Features & Enhancements\n\n')
        file.write(features_table_txt)
        file.write('\n%s Features listed\n\nBug Fixes\n\n' % str(features))
        file.write('Bug Fixes (merged)\n\n')        
        file.write(fixes_table_txt)
        file.write('\n%s Bugs listed\n\n' % str(fixes))
        file.write('Uncategorised Merged PRs\n\n')
        file.write(dontknow_table_txt)
        file.write('\n%s uncategorised issues listed\n\n' % str(uncategorised))
        file.write('Old PRs still open\n\n')
        file.write(old_pr_txt)
        file.write('\n%s Old PRs listed\n\n' % str(old_prs))
    file.close()
    print(("\nTable has been output to %s\n\n" % prs_file))
