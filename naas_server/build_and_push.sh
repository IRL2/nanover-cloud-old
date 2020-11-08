#!/bin/bash -e
docker build -t eu.gcr.io/narupa-web-ui/narupa-web-ui:latest .
docker push eu.gcr.io/narupa-web-ui/narupa-web-ui:latest