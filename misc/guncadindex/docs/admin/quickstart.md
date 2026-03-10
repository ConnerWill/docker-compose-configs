# Quickstart

This quickstart guide will get a local GunCAD Index instance up and running as fast as possible.

For detailed documentation, see [`deployment.md`](./deployment.md).

## Local Use

1. Clone the repository and `cd` into it. This can be done with Git: `git clone https://gitlab.com/guncad-index/index && cd index`

2. Copy `.env-template` to `.env` and open it in a text editor. Review it and change any values you like, consulting [`deployment.md`](./deployment.md) for details. At a minimum, you will need to set some secrets for the site and database

3. Download and launch the Index by running `docker compose up -d`

5. Once live, the app should be available [here](http://localhost:8265)

Once the app's up, you should consider doing some basic tasks:

* [Add an admin user](./adding-admin.md)
* Wait. It will take some time for data to pour in. The instance should seed itself off of a master list of channels and then begin scraping for content, which may take upwards of an hour the first time. It is normal to not have thumbnails until the initial indexing pass is complete.

## Online Use

If you intend on hosting this application over the open internet, you should do the following:

* Purchase a domain
* Set up HTTPS
* Firewall off 8265 (or modify the compose file to not listen on `0.0.0.0`)
