# pihole-wireguard-unbound

<!--toc:start-->
- [pihole-wireguard-unbound](#pihole-wireguard-unbound)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Configuration](#configuration)
    - [.env File](#env-file)
<!--toc:end-->

## Requirements

- `docker`
- `docker-compose`

## Installation

```bash
sudo -s <<< 'mkdir -p /opt/docker && chown -R $(whoami):docker /opt/docker'
cd /opt/docker && git clone https://github.com/ConnerWill/docker-compose-configs.git
```

## Configuration

### .env File

Configuration can be done by copying the `./EXAMPLE.env` file to `./.env` and then modifying the values.

```bash
cp ./EXAMPLE.env ./.env
```

> [!NOTE]
> When changing configuration values in `./.env`, make sure to change values in the other configuration files *(e.g. `./unbound/unbound.conf`)*.
