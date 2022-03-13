FROM python:3.8-slim-buster

RUN mkdir /flask

COPY requirements.txt /flask

WORKDIR /flask

RUN pip install -r requirements.txt

COPY . /flask

EXPOSE 5001