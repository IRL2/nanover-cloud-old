#!/bin/bash

gcloud beta compute --project=narupa-web-ui instances create narupa-web-ui \
	--zone=europe-west2-a \
	--machine-type=f1-micro \
	--subnet=default \
	--network-tier=PREMIUM \
	--maintenance-policy=MIGRATE \
	--scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
	--tags=narupa-web \
	--image=debian-10-buster-v20200714 \
	--image-project=debian-cloud \
	--boot-disk-size=10GB \
	--boot-disk-type=pd-standard \
	--boot-disk-device-name=narupa-web-ui \
	--no-shielded-secure-boot \
	--shielded-vtpm \
	--shielded-integrity-monitoring \
	--reservation-affinity=any


gcloud compute ssh narupa-web-ui -- 'curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && rm -f get-docker.sh && sudo usermod -aG docker mark'
gcloud compute ssh narupa-web-ui -- 'sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose'
gcloud compute ssh narupa-web-ui -- 'mkdir -p data/{nginx,docker,app}'

gcloud compute scp nginx.live.conf narupa-web-ui:data/nginx/app.conf
gcloud compute scp docker-compose.live.yml narupa-web-ui:docker-compose.yml
gcloud compute scp init-letsencrypt.sh narupa-web-ui:init-letsencrypt.sh

gcloud compute ssh narupa-web-ui -- '/bin/bash init-letsencrypt.sh'

echo "Now do the following:"
echo "\t- ssh onto the box with: gcloud compute ssh narupa-web-ui"
echo "\t- copy the firebase admin sdk key json file into ~/data/app/narupa-web-firebase-adminsdk.json"
echo "\t- copy the google cloud key json file into ~/data/app/narupa-web.json"