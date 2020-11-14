FROM python:3.8-slim-buster

COPY bin /opt/
RUN pip install pip==20.0.2 --no-cache-dir && pip install docopts pygithub prettytable pygit2 && apt update && apt install -y git nano && apt clean && cp /opt/startup.sh /usr/bin/startup.sh && chmod +x /usr/bin/startup.sh

#ENTRYPOINT ["startup.sh"]
CMD ["startup.sh"]
