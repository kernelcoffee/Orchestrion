# Gandi

This module updates Gandi DNS record using the LiveDNS API

Inspired by https://github.com/cavebeat/gandi-live-dns

## Prequisites
- Go to your Gandi account security page: https://account.gandi.net/en/users/USER/security (where USER is your username)
- Generate your API key, to be copied into your configuration file

## References
- https://doc.livedns.gandi.net/

# Config
Add this section to you config file to enable it.

```
[gandi-dyndns]
interval=30
api_secret=<secrect_key>
domain=<domain_name>
subdomains=<subdomain1>,<subdomain2>
```
