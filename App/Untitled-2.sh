#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

source config

admin_password=""
dry_run=false
offline_install=false
upgrade=false

FILES=(
  "./isg-index/opensearch.yml"
  "./isg-dashboard/dashboards.yml"
  "./isg-tools/isg_tools.json"
  "./isg-ingest/etc/fluent.conf"
  "./isg-ingest/etc/conf.d/output_opensearch.conf"
  "./isg-index/opensearch-security/roles_mapping.yml"
)

# Backup the files before processing
for file in "${FILES[@]}"; do
  dir=$(dirname "$file")
  filename=$(basename "$file")
  base="${filename%.*}"
  ext="${filename##*.}"
  new_file="$dir/$base.original.$ext"

  if [[ ! -f "$new_file" ]]; then
    cp "$file" "$new_file"
  fi
done

CERT_DIRS=(
  "./isg-index"
  "./isg-dashboard"
  "./isg-cron"
  "./isg-tools"
  "./isg-ingest"
)


# Generate certificates if rootca is not provided
if [ ! -f "./certificates/rootca.pem" ]; then
  ./certificates/generate_certs.sh
  # update isg-tools to not do cert validation
  sed -i 's/"insecure": false/"insecure": true/' ./isg-tools/isg_tools.json
fi

for dir in "${CERT_DIRS[@]}"; do
  cp -r ./certificates $dir
done

for arg in "$@"
do
  case $arg in
    --dry)
      dry_run=true
      ;;
    --offline)
      offline_install=true
      ;;
    --upgrade)
      upgrade=true
      ;;
    *)
      ;;
  esac
done

# opensearch.yml
sed -i \
  -e "s|ADMIN_DN|\"$admin_cert_dn\"|g" \
  -e "s|OPENSEARCH_NODE_CERTIFICATE|\"$node_cert_name\"|g" \
  -e "s|OPENSEARCH_NODE_KEY|\"$node_key_name\"|g" \
  -e "s|OPENSEARCH_ROOT_CA|\"rootca.pem\"|g" \
  "./isg-index/opensearch.yml"

# opensearch_dashboards.yml
sed -i \
  -e "s|OPENSEARCH_ROOT_CA|\"/usr/share/opensearch-dashboards/certificates/rootca.pem\"|g" \
  -e "s|DASHBOARD_CLIENT_CERT|\"/usr/share/opensearch-dashboards/certificates/dashboard-client.pem\"|g" \
  -e "s|DASHBOARD_CLIENT_KEY|\"/usr/share/opensearch-dashboards/certificates/dashboard-client-key.pem\"|g" \
  -e "s|DASHBOARD_SERVER_CERT|\"/usr/share/opensearch-dashboards/certificates/dashboard-server.pem\"|g" \
  -e "s|DASHBOARD_SERVER_KEY|\"/usr/share/opensearch-dashboards/certificates/dashboard-server-key.pem\"|g" \
  "./isg-dashboard/dashboards.yml"

# isg_tools.json
sed -i \
  -e "s|OPENSEARCH_ROOT_CA|/certificates/rootca.pem|g" \
  -e "s|ISG_SERVICE_CERT|/certificates/isg-service.pem|g" \
  -e "s|ISG_SERVICE_KEY|/certificates/isg-service-key.pem|g" \
  "./isg-tools/isg_tools.json"

# fluentd ingest
sed -i \
  -e "s|OPENSEARCH_ROOT_CA|\"/etc/td-agent/oscerts/rootca.pem\"|g" \
  -e "s|FLUENT_SERVER_CERT|\"/etc/td-agent/oscerts/ingest-server.pem\"|g" \
  -e "s|FLUENT_SERVER_KEY|\"/etc/td-agent/oscerts/ingest-server-key.pem\"|g" \
  "./isg-ingest/etc/fluent.conf"

# TODO: This is for backwards compatibility for now
# output_opensearch part 1 - fluentd service

sed -i \
    -e "s/^# ca_file \"#{ENV\['OPENSEARCH_ROOT_CA'\]}\"/ca_file OPENSEARCH_ROOT_CA/" \
    -e "s/^# client_cert \"#{ENV\['OPENSEARCH_CLIENT_CERT'\]}\"/client_cert ISG_SERVICE_CERT/" \
    -e "s/^# client_key \"#{ENV\['OPENSEARCH_CLIENT_KEY'\]}\"/client_key ISG_SERVICE_KEY/" \
    "./isg-ingest/etc/conf.d/output_opensearch.conf"

# output_opensearch part 2 - fluentd service
sed -i \
  -e "s|OPENSEARCH_ROOT_CA|\"/certificates/rootca.pem\"|g" \
  -e "s|ISG_SERVICE_CERT|\"/certificates/isg-service.pem\"|g" \
  -e "s|ISG_SERVICE_KEY|\"/certificates/isg-service-key.pem\"|g" \
  "./isg-ingest/etc/conf.d/output_opensearch.conf"

# roles_mapping
sed -i \
  -e "s|ISG_SERVICE_CN|$isg_service_cert_cn|g" \
  -e "s|DASHBOARD_CLIENT_CN|$dashboard_client_cert_cn|g" \
  "./isg-index/opensearch-security/roles_mapping.yml"

# Update permissions for opensearch
chmod 0700 ./isg-index/opensearch-security
chmod 0600 ./isg-index/opensearch-security/*.yml
chmod 0600 ./isg-index/opensearch.yml

import_saved_obj(){
	echo "Import dashboards"
	err=$( curl -k -o /dev/null -w %{http_code} -X POST "https://localhost/analytics/api/saved_objects/_import?overwrite=true" -H "securitytenant: global" -H "osd-xsrf: true" --form file=@isg-dashboard/ISG-Dashboard-SavedObjects.ndjson -u "admin:$admin_password" );
	if [ "$err" -ne 200 ]
	then
		echo "query failed with HTTP error $err"
	else
		echo "Dashboards successfully imported."
	fi
}


post_install(){
  # Create admin
  docker exec node1 curl -H 'Content-Type: application/json' \
                         -X PUT "https://node1:9200/_plugins/_security/api/internalusers/admin" \
                         --cert "/usr/share/opensearch/config/admin.pem" \
                         --key "/usr/share/opensearch/config/admin-key.pem" \
                         --cacert "/usr/share/opensearch/certificates/rootca.pem" \
                         -s \
                         -k \
                         -d '{
                               "password": "'"$admin_password"'",
                               "backend_roles": ["admin"]
                             }'

  # Give time to opensearch to actually create the admin user
  sleep 5
  # Import saved objects
  import_saved_obj
  # Give time to opensearch to actually create the saved objects.
  sleep 5
  # run isg_cli 
  chmod +x ./isg-index/isg_cli
  ./isg-index/isg_cli migrate -u 'admin' -p "$admin_password" -k  
}


main() {
  # Determine if we should use 'docker compose' or 'docker-compose'
  if docker-compose version >/dev/null 2>&1; then
    docker_compose_cmd="docker-compose"
  elif docker compose version >/dev/null 2>&1; then
    docker_compose_cmd="docker compose"
  else
      echo "Docker Compose is not installed on this system."
      exit 1
  fi

  if [ -z "$admin_password" ]; then
      while true; do
      read -sp "Please enter the admin password: " admin_password
      echo
          read -sp "Please re-enter the admin password for verification: " admin_password_verify
          echo

          if [ "$admin_password" != "$admin_password_verify" ]; then
              echo "Passwords do not match, please try again."
              continue
          fi

          if ! [[ ${#admin_password} -ge 12 && "$admin_password" =~ [A-Z] && "$admin_password" =~ [a-z] && "$admin_password" =~ [0-9] && "$admin_password" =~ [[:punct:]] ]]; then
              echo "Password must be at least 12 characters long and must contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
              continue
          fi

          break
      done
  fi

  if [ "$offline_install" = true ]; then
    echo "Offline install"
    docker load -i isg_agilesec_analytics.tar
    $docker_compose_cmd -f docker-compose-offline.yml up -d --force-recreate
  else
    echo "Online install"
    command="$docker_compose_cmd up -d --force-recreate"
    if [ "$upgrade" = true ]; then
      command="$command --build"
    fi
    $command
  fi


  # Define an array with the container names or IDs you want to check
  CONTAINERS=("node1" "isg-dashboard" "isg-ingest" "isg-proxy")

  # Function to check the health status of specific containers
  check_specific_containers_healthy() {
      for CONTAINER in "${CONTAINERS[@]}"; do
          # Get the health status of each container
          HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null)

          if [ "$HEALTH_STATUS" != "healthy" ]; then
              # If any container is not healthy, return 1
              echo "Container $CONTAINER is still $HEALTH_STATUS"
              return 1
          fi
      done

      # If all containers are healthy, return 0
      return 0
  }
  # Loop until all specific containers are healthy
  echo "Waiting for specific containers to be healthy..."
  while ! check_specific_containers_healthy; do
      echo "Some containers are still starting or unhealthy, waiting..."
      sleep 5 # Wait for 5 seconds before checking again
  done

  echo "All specified containers are healthy!"

  post_install
}

if [ "$dry_run" = false ]; then
  main
fi
