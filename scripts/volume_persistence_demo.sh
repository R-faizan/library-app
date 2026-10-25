#!/bin/bash
# ---------------------------------------------------------------------------
# Task 4 - Prove data persists in the named volume after containers are
#          destroyed and recreated.
#   cd /opt/library-app && bash scripts/volume_persistence_demo.sh
# ---------------------------------------------------------------------------
run() { echo -e "\n\$ $*"; eval "$@"; }
BOOK="Persistence Test $(date +%H%M%S)"

echo "===== Step 1: the named volume ====="
run docker volume ls
run docker volume inspect library_mysql_data

echo -e "\n===== Step 2: add a record ====="
run "curl -s -o /dev/null -w 'HTTP %{http_code}\n' -X POST -d 'title=$BOOK&author=Volume Demo' http://localhost/add"
run "curl -s http://localhost/api/books | grep -o '\"title\":\"$BOOK\"'"

echo -e "\n===== Step 3: DESTROY the containers (volume is kept) ====="
OLD_ID=$(docker inspect -f '{{.Id}}' library-db | cut -c1-12)
run docker compose down
run docker ps -a --filter name=library
run docker volume ls \| grep mysql_data

echo -e "\n===== Step 4: RECREATE the containers ====="
run docker compose up -d
echo "Waiting for MySQL + web to be healthy..."
for i in $(seq 1 30); do curl -sf http://localhost/health >/dev/null && break; sleep 3; done
NEW_ID=$(docker inspect -f '{{.Id}}' library-db | cut -c1-12)
echo "Old db container ID: $OLD_ID   New db container ID: $NEW_ID  (different containers)"

echo -e "\n===== Step 5: the record is STILL there ====="
if curl -s http://localhost/api/books | grep -q "$BOOK"; then
  echo "SUCCESS: '$BOOK' survived container recreation -> data lives in the volume"
else
  echo "FAILED: record not found"
fi

# Also show it directly from MySQL inside the new container
run "docker exec library-db sh -c 'mysql -u\$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE -e \"SELECT id,title FROM books;\"' 2>/dev/null"
