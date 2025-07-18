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

#### .env File Example

```Dotenv
# shellcheck disable=SC2148,SC1073,SC2034

# Time zone configuration for containers
TIME_ZONE=America/Chicago

# Network settings for Docker Compose
NETWORK_DRIVER=bridge                       # Use bridge network driver for container communication
NETWORK_SUBNET=10.14.14.0/24                # Subnet for the custom Docker network

# WireGuard VPN configuration
WIREGUARD_ALLOWED_IPS=0.0.0.0/0             # Allow all IP ranges for WireGuard traffic
WIREGUARD_CONFIG_DIR=/opt/docker/docker-compose-configs/pihole-wireguard-unbound/wireguard  # Directory for WireGuard configuration files
WIREGUARD_CONTAINER_NAME=pihole-wireguard   # Name of the WireGuard container
WIREGUARD_IMAGE_NAME=lscr.io/linuxserver/wireguard:latest  # WireGuard image to use
WIREGUARD_INTERNAL_SUBNET=10.13.13.0        # Internal subnet for WireGuard VPN
WIREGUARD_IPV4_ADDRESS=10.14.14.3           # IPv4 address for the WireGuard container
WIREGUARD_PEERS=2                           # Number of WireGuard peers (clients)
WIREGUARD_SERVER_PORT=51820                 # Port for WireGuard server
WIREGUARD_SERVER_URL=pihole.example.com     # Public URL for the WireGuard server

# Pi-hole configuration
PIHOLE_CONTAINER_NAME=pihole-pihole         # Name of the Pi-hole container
PIHOLE_DNSMASQ_DIR=/opt/docker/docker-compose-configs/pihole-wireguard-unbound/etc-dnsmasq.d  # Directory for Pi-hole DNSMasq config
PIHOLE_DNSMASQ_LISTENING=all                # DNSMasq listening behavior (all interfaces)
PIHOLE_ETC_DIR=/opt/docker/docker-compose-configs/pihole-wireguard-unbound/etc-pihole  # Directory for Pi-hole configuration
PIHOLE_FTLCONF_DNS_LISTENINGMODE=all        # Pi-hole FTL DNS listening mode
PIHOLE_IMAGE_NAME=pihole/pihole:latest      # Pi-hole image to use
PIHOLE_IPV4_ADDRESS=10.14.14.2              # IPv4 address for the Pi-hole container
PIHOLE_WEBUI_PASSWORD=changeme              # Password for Pi-hole Web UI (change this for security)

# Unbound DNS resolver configuration
UNBOUND_CONFIG_DIR=/opt/docker/docker-compose-configs/pihole-wireguard-unbound/unbound  # Directory for Unbound configuration
UNBOUND_CONTAINER_NAME=pihole-unbound       # Name of the Unbound container
UNBOUND_IMAGE_NAME=mvance/unbound:latest    # Unbound image to use
UNBOUND_IPV4_ADDRESS=10.14.14.4             # IPv4 address for the Unbound container

```
