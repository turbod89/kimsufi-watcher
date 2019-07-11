FROM python:3-alpine

WORKDIR /code

RUN apk update && \
# Install build dependencies
    apk add --no-cache --virtual build-deps \
        python-dev \
        pcre-dev \
        gcc \
        musl-dev \
        git \
        linux-headers \
        jpeg-dev \
        zlib-dev \
        libffi-dev \
        make \
# Install OS requirements
    && apk add \
        libffi \
        jpeg \
        zlib \
        pcre \
        mailcap \
        mariadb-dev \
        mariadb-client \
    && pip install --no-cache-dir virtualenv \
    && virtualenv /env

ADD requirements.txt /code/requirements.txt

# Install requirements
RUN /env/bin/pip install --no-cache-dir -r /code/requirements.txt

# Clean up build dependencies
RUN apk del build-deps && rm -rf /root/.cache

ADD . /code/