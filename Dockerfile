FROM python:3.6-alpine

COPY tap_linkedin/schemas/ /opt/app/tap_linkedin/schemas/
COPY setup.py /opt/app/

WORKDIR /opt/app/

RUN pip install -e .

CMD ["tap-linkedin", "-c", "config.json", "--catalog", "catalog.json"]