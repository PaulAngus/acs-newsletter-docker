FROM python:3.8-slim-buster

RUN pip install pip==20.0.2 --no-cache-dir && pip install docopts pygithub prettytable pygit2 
COPY analyse_git.py startup.sh /opt/

ENTRYPOINT ["startup.sh"]
CMD ["startup.sh"]
