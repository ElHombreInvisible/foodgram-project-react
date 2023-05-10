FROM python:3.11-slim

WORKDIR /

COPY ./ ./

RUN pip3 install -r requirements.txt --no-cache-dir

RUN apt-get update && \
apt-get install -y wkhtmltopdf && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

CMD [ "python3", "manage.py", "runserver", "0:8000" ]