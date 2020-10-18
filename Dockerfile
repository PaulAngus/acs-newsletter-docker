FROM python:3.8-slim-buster

RUN pip install docopts pygithub && curl https://raw.githubusercontent.com/shapeblue/cloudstack-www/master/data/newsletter.txt --output /opt/newsletter.txt
COPY wip.py features_merged.py bug_fixes_merged.py startup.sh ./lib/ /opt/

ENTRYPOINT ["startup.sh"]
CMD ["startup.sh"]
