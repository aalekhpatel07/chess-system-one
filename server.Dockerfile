FROM python:3.14 AS base
RUN apt-get update -y && apt-get upgrade -y
RUN python3.14 -m venv /var/venv/app
RUN /var/venv/app/bin/pip install "von-sdk"
EXPOSE 80
CMD ["/var/venv/app/bin/von", "serve", "--host", "0.0.0.0", "--port", "80"]
