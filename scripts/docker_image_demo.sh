#!/bin/bash
# ---------------------------------------------------------------------------
# Task 3 - Docker installation check, build a custom image, run a container
#   cd /opt/library-app && bash scripts/docker_image_demo.sh
# ---------------------------------------------------------------------------
run() { echo -e "\n\$ $*"; eval "$@"; }

run docker --version
run docker compose version
run systemctl is-active docker

# Build the custom image from app/Dockerfile and tag it
run docker build -t library-web:1.0 ./app
run docker images library-web
run docker history library-web:1.0 \| head -12      # the layers of the image

# Run it standalone (no MySQL -> it uses its built-in SQLite fallback) on port 8080
run docker rm -f web-test 2\>/dev/null
run docker run -d --name web-test -p 8080:5000 library-web:1.0
sleep 5
run docker ps --filter name=web-test
run curl -s http://localhost:8080/health
run docker logs --tail 5 web-test
run docker exec web-test whoami                    # shows non-root user "appuser"

# Clean up the test container (image stays)
run docker stop web-test
run docker rm web-test
