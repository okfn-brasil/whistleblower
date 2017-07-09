FROM python:3.6.1

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN useradd -ms /bin/bash serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor

COPY server.py ./
CMD flask run --host=0.0.0.0
