FROM python:3.6.1

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
RUN ./rosie/setup

RUN useradd -ms /bin/bash serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor
