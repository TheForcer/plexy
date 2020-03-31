FROM python:3.8

LABEL name="Plexy"
LABEL authors="Felix"
LABEL description="Matrix bot for Plex and Ombi"

ADD requirements.txt /opt/
RUN pip3 install -r /opt/requirements.txt

ADD . /opt/
VOLUME ["/opt/config", "/opt/data"]

CMD [ "python3", "/opt/main.py" ]