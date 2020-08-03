FROM python:3.6-slim-buster

RUN apt update
RUN apt install -y git gcc

WORKDIR /minerva

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY minerva.py .
COPY config/test/.minerva /root/

ENTRYPOINT [ "python", "./minerva.py" ]