FROM python:3.8-slim-buster

RUN pip install docopts pygithub prettytable pygit2
COPY analyse_git.py startup.sh /opt/

ENTRYPOINT ["startup.sh"]
CMD ["startup.sh"]
