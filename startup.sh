#!/bin/bash
set -e

curl https://raw.githubusercontent.com/shapeblue/cloudstack-www/master/data/newsletter.txt --output /opt/newsletter.txt

cd /opt && python analyse_git --config=conf.txt
