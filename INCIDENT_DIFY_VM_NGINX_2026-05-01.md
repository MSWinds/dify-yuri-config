# Incident: Dify HTTPS Outage After VM Reboot

Date: 2026-05-01 UTC

## Summary

`https://dify.cgu.edu/apps` became unavailable after the VM rebooted. DNS and the wildcard CGU TLS certificate were still valid. The outage was caused by the host-level Ubuntu `nginx.service` auto-starting after reboot and interfering with the Docker-managed Dify nginx container.

## Impact

- Public HTTPS access to Dify failed.
- HTTP reached the VM but served the default Ubuntu nginx site instead of Dify.
- Dify backend services, database, Redis, and web containers were mostly healthy.

## Evidence

- `dify.cgu.edu` still resolved to `134.173.236.205`.
- Port 443 returned connection refused before recovery.
- Port 80 returned `Server: nginx/1.24.0 (Ubuntu)` and a default-site response.
- The Dify nginx container initially failed with:

```text
host not found in upstream "api" in /etc/nginx/conf.d/default.conf
```

- After cleanup, the nginx container was briefly in a partial state: running, but with no Docker networks and no published ports.

## Root Cause

The VM reboot caused the host-level `nginx.service` to start automatically. That service occupied port 80 and served the Ubuntu default nginx site. The intended production entrypoint is the Docker-managed `docker-nginx-1` container, which must bind ports 80 and 443 and use the existing CGU wildcard certificate mounted from `docker/nginx/ssl`.

## Recovery

The host-level nginx service was disabled/stopped, then the Docker nginx container was force-recreated so Docker could reattach networks and publish ports cleanly:

```bash
sudo systemctl disable --now nginx
cd /home/kaijiey/github_projects/dify-yuri-config/docker
docker compose up -d --force-recreate --no-deps nginx
```

Verification after recovery:

```text
docker-nginx-1 -> 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
https://dify.cgu.edu/apps -> HTTP/1.1 200 OK
TLS certificate -> CN=*.cgu.edu, verification OK
```

## Prevention

- Keep host-level `nginx.service` disabled on this VM unless it is intentionally used as the public reverse proxy.
- After VM reboots, verify:

```bash
docker ps
ss -ltnp | grep -E ':(80|443)\s'
curl -Ik https://dify.cgu.edu/apps
```

- If Docker nginx is running but has no published ports or no networks, recreate only the nginx container:

```bash
cd /home/kaijiey/github_projects/dify-yuri-config/docker
docker compose up -d --force-recreate --no-deps nginx
```
