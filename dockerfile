FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git iproute2 iputils-ping util-linux python3 python3-pip python3.10-venv

COPY ./ /manager
WORKDIR /manager


RUN python3 -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r /manager/requirements.txt


ENV PATH="/manager/venv/bin:$PATH"

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
