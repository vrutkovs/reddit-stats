FROM fedora:25

RUN dnf install -y python3-pip git && \
    git clone https://github.com/vrutkovs/reddit-stats /reddit-stats && \
    dnf clean all

WORKDIR reddit-stats
RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD ["python3", "webserver.py"]
