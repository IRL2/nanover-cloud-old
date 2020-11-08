#!/bin/bash -e
gcloud config set project narupa-web-ui
gcloud compute ssh narupa-web-ui -- 'docker-compose pull && docker-compose up -d && docker-compose restart nginx'
