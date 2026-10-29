FROM mvance/unbound:latest

RUN apt-get update && \
    apt-get install -y gettext-base

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
