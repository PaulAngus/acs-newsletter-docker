

Git Summary
===========

Premise:
========

Self contained environment to:

1. create the tables which are used in a release's release notes to detail the changes that have been made since the last release.
2. use the above tables in conjuction with a version controlled text file which will form a periodic newsletter to the CloudStack mailing lists (and potentially beyond)

The PRs (open and closed) will be categorised via the labels attached to them

NOTE: analysis_git.py is designed to run outside of the surrounding app, so var initialisation will look a little clunky 

Label categorisation:

---------------------
(TODO - documentation)

Requires
--------

python3.8 + docopt pygithub prettytable gitpython


Task list
---------

- [x] create python script to generate tables
- [x] create lightweight docker build file with python dependancies installed
- [ ] [IN PROGRESS]- create multi-purpose entrypoint
- [ ] Determine parameters required to specify the action to carry out and the parameters those actions require
- [ ] Determine simplest/most user freindly way to get those parameters into the container at or before startup.
- [ ] Determine simplest/most user freindly way to get the results to the user
- [ ] Deterine the best way to get the output to the CloudStack mailing lists and possibly to outside mailing lists.





Brain dump of commands:
-----------------------

BUILD_KIT=1 docker build --tag acsn:0.1 .

docker run --env-file env.vars acsn  #untried