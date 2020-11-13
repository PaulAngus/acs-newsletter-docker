FROM python:3.8-slim-buster

RUN pip install pip==20.0.2 --no-cache-dir && pip install docopts pygithub prettytable pygit2 
COPY bin /opt/

#ENTRYPOINT ["/opt/bin/startup.py"]
#CMD ["/opt/bin/startup.py"]
