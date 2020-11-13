#!/bin/python

import urllib.request
import os
from bin import create_config

#working_dir = os.getenv('destination')

# grab the newslater 'news'
#url = 'https://raw.githubusercontent.com/shapeblue/cloudstack-www/master/data/newsletter.txt'
#urllib.request.urlretrieve(url, '/tmp/newsletter.txt')

# grab env vars


# run the PR and Commit generation
#working_dir = os.environ.get('destination')
#config_file = f"{working_dir}/conf.txt"
#os.system("analyse_git.py --config=" + config_file)

# combine files
#filenames = ["/tmp/newsletter.txt", "/tmp/prs.txt"]
#final_file = f"{working_dir}/newsletter.txt"

#with open(final_file, "w") as outfile:
#    for filename in filenames:
#        with open(filename) as infile:
#            contents = infile.read()
#            outfile.write(contents)

# cleanup
#os.remove("/tmp/newsletter.txt")
#os.remove("/tmp/prs.txt")

