FROM fedora:25

RUN dnf update -y && \
    dnf install -y python3-pip git && \
    git clone https://github.com/vrutkovs/reddit-stats /reddit-stats && \
    dnf clean all

WORKDIR reddit-stats
RUN pip3 install -r requirements.txt && \
    git log -1 --pretty=format:'%h - %s (%ci)' --abbrev-commit > templates/commit.jinja2

ADD praw.ini /reddit-stats

EXPOSE 8080

CMD ["python3", "webserver.py"]
