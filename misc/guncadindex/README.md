<div align="center">
![Logo](docs/images/gci-icon-round.png)

[![Latest Release](https://gitlab.com/guncad-index/index/-/badges/release.svg)](https://gitlab.com/guncad-index/index/-/releases) [![pipeline status](https://gitlab.com/guncad-index/index/badges/master/pipeline.svg)](https://gitlab.com/guncad-index/index/-/commits/master) [![coverage report](https://gitlab.com/guncad-index/index/badges/master/coverage.svg)](https://gitlab.com/guncad-index/index/-/commits/master)
<h1>GunCAD Index</h1>
A search engine for guns

[Click here to visit the site](https://guncadindex.com)
</div>

## Overview

GunCAD Index is a search engine for guns. It spiders the LBRY network for files that look like 3D-printable firearm designs and related accessories, indexing and tagging them. It has a number of features to make this process quick, easy, and independent of Odysee.

## Quickstart

> [!warning]
> This software, while it does not distribute 3D-printable guns files directly, *does* closely interact with repositories and *will* download metadata about releases. Depending on your jurisdiction, this metadata may be illegal for you to possess and/or redistribute.

If you'd like to run this software yourself, see [the Quickstart Guide here](./docs/admin/quickstart.md). It's almost brainless for a local, personal instance:

```bash
git clone https://gitlab.com/guncad-index/index
cd index
cp .env-template .env
vim .env # Read the comments, edit the config
docker compose up -d
```

## Documentation

Detailed documentation can be viewed [at `./docs`](./docs), whether you're an end-user, administrator, or potential contributor.

## Contributing

Want to help out? We'd be happy to have you.

Review [`CONTRIBUTING.md`](/CONTRIBUTING.md) and pick an issue from the list.

## License

This software is distributed under the terms of the [GNU Affero General Public License](/LICENSE.md).

### Third-Party Licenses

"IBM Plex Sans" and "IBM Plex Mono" Copyright © 2017 IBM Corp. with Reserved Font Name "Plex" licensed under the terms of [SIL Open Font License, Version 1.1](https://openfontlicense.org/open-font-license-official-text/)

[Heroicons](https://github.com/tailwindlabs/heroicons) is licensed under the terms of the [MIT License](https://github.com/tailwindlabs/heroicons/blob/master/LICENSE).
