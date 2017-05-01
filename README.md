# Whistleblower

*Still under development. Although all the pieces seem to properly work separately, the code isn't 100% connected. There isn't - yet - a single command to run and get suspicious reimbursements to a Twitter account.*

Follow [@RosieDaSerenata](https://twitter.com/RosieDaSerenata) to get Brazilian Chamber of Deputies' updates in your timeline.

## Setup

```console
$ git clone --recursive git@github.com:Irio/whistleblower.git
$ conda create --name serenata_whistleblower python=3
$ conda activate serenata_whistleblower
$ pip install -r requirements.txt
$ cp .env.example .env
$ ./rosie/setup
```

## Running

```
$ python src/dataset.py
$ python rosie/rosie.py run chamber_of_deputies data
```
