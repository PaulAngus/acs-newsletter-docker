FROM python:3.8-slim-buster

RUN pip install docopts pygithub prettytable
COPY analyse_git.py startup.sh ./lib/ /opt/

ENTRYPOINT ["startup.sh"]
CMD ["startup.sh"]
