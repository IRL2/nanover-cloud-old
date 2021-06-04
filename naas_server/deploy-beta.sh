#!/bin/bash -e
gcloud config set project narupa-web-ui
gcloud compute scp ./infra/beta/docker-compose.beta.yml narupa-web-ui-beta:docker-compose.yml
gcloud compute ssh narupa-web-ui-beta -- 'docker-compose pull && docker-compose up -d && docker-compose restart nginx'
