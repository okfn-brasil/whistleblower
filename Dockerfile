FROM python:3.6.1

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN mkdir rosie
COPY rosie/config.ini.example ./config.ini
COPY rosie/requirements.txt ./rosie
RUN pip install -r rosie/requirements.txt

COPY . .

RUN useradd -ms /bin/bash serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor
