import subprocess
import re
from datetime import datetime
from lib.commits_from_gitlog import commitlist
import string

# run the code...
if __name__ == '__main__':

    #repoClone = pygit2.clone_repository(repo.git_url, '/tmp/cloudstack', bare='True', depth=1)

    leading_4_spaces = re.compile('^    ')
    previous_commit_datestr = '01-01-2020'
    previous_commit_date = datetime.strptime(previous_commit_datestr, '%m-%d-%Y').date()
    commits = commitlist.get_commits()
    for commit in commits:
        thiscommit = commit['title']
        reverted = re.match('^Revert "', thiscommit)
        if reverted:
            commitdatestr = commit['date']
            print(commitdatestr)
            date_time_str = ' '.join(commitdatestr.split(" ")[:-1])
            commitdate = datetime.strptime(date_time_str, '%c').date()
            if commitdate > previous_commit_date:
                revertedcommit = re.search('.*This reverts commit ([A-Za-z0-9]*).*', commit['message'])
                print(revertedcommit.group(1))
