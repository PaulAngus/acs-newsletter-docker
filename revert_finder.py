import subprocess
import re
from datetime import datetime
from lib.commits_from_gitlog import commitlist
import string

# run the code...
if __name__ == '__main__':
        
    previous_commit_datestr = '01-01-2020'
    previous_commit_date = datetime.strptime(previous_commit_datestr, '%m-%d-%Y').date()
    commits = commitlist.get_commits()
    for commit in commits:
        thiscommit = commit['title']
        reverted = re.match('^Revert "', thiscommit)
        if reverted:
            commitdatestr = commit['date']
            date_time_str = ' '.join(commitdatestr.split(" ")[:-1])
            commitdate = datetime.strptime(date_time_str, '%c').date()
            if commitdate > previous_commit_date:
                commitmsgstr = " ".join(commit['message'].split("\n")[:-3])
                print(commitmsgstr)
                revertedcommit = re.compile('.*This reverts commit ([A-Za-z0-9]*).*', commitmsgstr)
                result = revertedcommit.search(commitmsgstr)
                print(result.group(1))
