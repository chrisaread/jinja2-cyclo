FROM python:2.7.14

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY cyclo.py /usr/share

VOLUME "/data"
WORKDIR "/data"
ENTRYPOINT ["python", "/usr/share/cyclo.py"]
