# docker image build -f Dockerfile -t twitter_cfdspace_bot:latest .
FROM python:3.9-alpine

COPY config.py /bot/
COPY __init__.py /bot/
COPY main.py /bot/
COPY api_helper.py /bot/
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /bot
CMD ["python3", "main.py"]
