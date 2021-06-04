#!/bin/bash -e
gcloud config set project narupa-web-ui
gcloud compute scp ./infra/live/docker-compose.live.yml narupa-web-ui:docker-compose.yml
gcloud compute ssh narupa-web-ui -- 'docker-compose pull && docker-compose up -d && docker-compose restart nginx'
