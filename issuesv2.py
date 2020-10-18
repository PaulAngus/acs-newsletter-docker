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
from lib.Table import TableRST, TableMD
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
    repo_name = args['--repo']
    prev_release_ver = args['--prev_release_ver']
    prev_release_commit = args['--prev_release_commit']
    new_release_ver = args['--new_release_ver']
    branch = args['--branch']

    gh_base_url = args['--gh_base_url']
    jira_base_url = args['--jira_base_url']
    jira_server_url = args['--jira_server_url']

#     table column widths
    branch_len = int(args['--col_branch_width'])
    gh_len = int(args['--col_github_width'])
    jira_len = int(args['--col_jira_width'])
    issue_type_len = int(args['--col_type_width'])
    issue_priority_len = int(args['--col_priority_width'])
    desc_len = int(args['--col_desc_width'])
    
    outputfile = str(os.path.splitext(args['--config'])[0])+".rst"
##
#     connect to jira and github
##    jira = JIRA({
##        'server': jira_server_url
##    })
##    gh = Github(gh_token)
##
#     get the repo and commits
##    repo = gh.get_repo(repo_name)
##    commits = repo.get_commits()
##
#     loop through the commits and pull relevant PR numbers
##    merged = []
##    reverted = []
##    for c in commits:
#         break when we hit the previous release commit
##        if c.sha == prev_release_hash:
##            break
##
#         get the first line of the commit message
##        commit_msg = c.commit.message.splitlines()[0]
##
#         make sure the commit is a PR merge (using the `git pr ####` tool)
##        if 'Revert "Merge pull request #' == commit_msg[0:28]:
#             eg: Revert "Merge pull request #1493 from shapeblue/nio-fix"
##            pr_num = int(commit_msg[28:].split(' ')[0]) # get the text until the next space and cast to int
##            if pr_num not in reversed:
##                reverted.append(pr_num)
##        if 'Merge pull request #' == commit_msg[0:20]:
#             eg: Merge pull request #1523 from nlivens/bug/CLOUDSTACK-9365
##            pr_num = int(commit_msg[20:].split(' ')[0]) # get the text until the next space and cast to int
##            if pr_num not in merged:
##                merged.append(pr_num)
##
#         make sure we pick up the PR merges which are done through Github
##        regex = r"\(#(\d+)\)$"
##        matches = re.findall(regex, commit_msg)
##        for match in matches:
##            if match not in merged:
##                merged.append(int(match))
##
#     removed reverted PRs from the merged list
##    merged = [pr for pr in merged if pr not in reverted]
        
    
    gh = Github(gh_token)
    #repo = gh.get_repo(repo_name)
    
    repo_tags = repo.get_tags()
    if prev_release_commit:
        print("Previous Release Commit SHA found, overriding pre_release_ver")
        prev_release_hash = prev_release_commit
    else:
        print("Finding commit SHA for previous version")
        for tag in repo_tags:
            if tag.name == prev_release_ver:
                prev_release_hash = tag.commit.sha
                print(("name: %s tag.sha: %s" % (tag.name, tag.commit.sha)))

    if not prev_release_hash:
        print("No starting point found via version tag or commit SHA")
        exit

    print(("Retrieving commits from %s" % branch))        
    commits = repo.get_commits(sha=(branch))
    
    merged = []
    reverted = []
    for c in commits:
        # break when we hit the previous release commit
        if c.sha == prev_release_hash:
            break

        print(("Adding commit %s" % c.sha))
        # get the first line of the commit message
        commit_msg = c.commit.message.splitlines()[0]
    
        # make sure the commit is a PR merge (using the `git pr ####` tool)
        if 'Revert "Merge pull request #' == commit_msg[0:28]:
            # eg: Revert "Merge pull request #1493 from shapeblue/nio-fix"
            pr_num = int(commit_msg[28:].split(' ')[0]) # get the text until the next space and cast to int
            if pr_num not in reversed:
                reverted.append(pr_num)
        if 'Merge pull request #' == commit_msg[0:20]:
            # eg: Merge pull request #1523 from nlivens/bug/CLOUDSTACK-9365
            pr_num = int(commit_msg[20:].split(' ')[0]) # get the text until the next space and cast to int
            if pr_num not in merged:
                merged.append(pr_num)
    
        # make sure we pick up the PR merges which are done through Github
        regex = r"\(#(\d+)\)$"
        matches = re.findall(regex, commit_msg)
        for match in matches:
            if match not in merged:
                merged.append(int(match))
    
    print("Removing reverted commits..")
# removed reverted PRs from the merged list
    merged = [pr for pr in merged if pr not in reverted]
    
    print("Creating table..")

# start building the table(s)
    table = None
    try:
        table = TableRST([
            ('Version', branch_len),
            ('Github', gh_len),
            ('Type', issue_type_len),
            ('Priority', issue_priority_len),
            ('Description', desc_len),
        ])
    except IOError as e:
        print(('ERROR: %s' % str(e)))

    md = TableMD([
        'new_release_ver',
        'Github',
        'Type',
        'Priority',
        'Description'
    ])

    # process all officially merged PRs
    links = []
    for pr_num in merged:
        pr = repo.get_pull(pr_num)
        # setup github pr url
        gh_url = '%s%s' % (gh_base_url, pr_num)
        links.append('.. _`#%s`: %s' % (pr_num, gh_url))
        # initialize the data using github pr data
        desc = pr.title.strip()
        branch = pr.base.ref
        issue_type = ''
        issue_priority = ''
        jira_ticket = ''
        jira_url = ''

#        # check if there is a jira ticket associated
#        jira_prefix = 'CLOUDSTACK-' # string to check for jira ticket
#        jira_issue_index = pr.title.upper().find(jira_prefix)
#        if jira_issue_index != -1: # has jira ticket
#            # parse out the jira ticket int from the text
#            jira_int = "".join(itertools.takewhile(str.isdigit, 
#                (pr.title[jira_issue_index + len(jira_prefix):]).encode('ascii', 'ignore')))
#            jira_ticket = '%s%s' % (jira_prefix, jira_int)
#            try:
#                # get the jira ticket from the api and override defaults
#                issue = jira.issue(jira_ticket, expand="names")
#                jira_url = '%s%s' % (jira_base_url, jira_ticket)
#                links.append('.. _%s: %s' % (jira_ticket, jira_url))
#                issue_type = issue.fields.issuetype.name
#                issue_priority = issue.fields.priority.name
#                desc = issue.fields.summary.strip()
#            except:
#                continue # move on if there is an issue getting the ticket
#
#        # add the branch details

        if table:
            try:
                table.add_row([
                    new_release_ver,
                    '`#%s`_' % pr_num,
                    issue_type,
                    issue_priority,
                    desc
                ])
            except IOError as e:
                print(('ERROR: %s' % str(e)))
        md.add_row([
            new_release_ver,
            '[#%s](%s)' % (pr_num, gh_url),
            issue_type,
            issue_priority,
            desc
        ])
    if table:
        file = open('%s.txt' % outputfile ,"w")
        file.write('\n.. cssclass:: table-striped table-bordered table-hover\n\n\n')
        file.write(table.draw())
        file.write('\n%s Issues listed\n\n' % len(merged))

# output the links we referenced earlier
    for link in links:
        file.write('%s \n' % link)
        file.write('')

#print(md.draw()) # draw a markdown version of table as well
    file.close()
    print(("Commit data output to %s" % outputfile))
    