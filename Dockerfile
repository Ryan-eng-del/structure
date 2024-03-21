FROM python:3.11-slim

WORKDIR /code

RUN apt-get update ;\
    apt-get install less; \
    apt-get install vim; \
    apt-get install -y --no-install-recommends python3-dev default-libmysqlclient-dev build-essential;\
    pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .