#!/bin/bash

dt=$(date '+%Y%m%d%H%M');
image_name="narupa-image-${dt}"
zone="europe-west2-a"

echo "Launching instance"

gcloud compute --project=narupa-web-ui instances create $image_name \
	--zone=$zone \
	--machine-type=n1-standard-1 \
	--subnet=default \
	--network-tier=PREMIUM \
	--maintenance-policy=TERMINATE \
	--scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
	--tags=$image_name \
	--image-family=ubuntu-minimal-2004-lts \
	--image-project=ubuntu-os-cloud \
	--boot-disk-size=50GB \
	--boot-disk-type=pd-standard \
	--boot-disk-device-name=$image_name \
	--no-shielded-secure-boot \
	--shielded-vtpm \
	--shielded-integrity-monitoring \
	--reservation-affinity=any \
	--accelerator type=nvidia-tesla-t4,count=1

echo "Waiting for instance to come up"
sleep 60

# We should be able to run this automatically, but for now, prompt for manual
#echo "Please run this command and follow the instructions: gcloud compute ssh $image_name"
#read -p "Once finished, press enter to continue"

# Update packages
gcloud compute scp 'update_simulation_image.sh' "$image_name:"
gcloud compute ssh $image_name -- 'sudo bash update_simulation_image.sh'

# echo "Stopping instance"
gcloud compute instances stop $image_name

# echo "Creating image"
gcloud compute images create $image_name --source-disk=$image_name  --source-disk-zone=$zone

# echo "Deleting instance"
gcloud compute instances delete $image_name --delete-disks=all --quiet --zone=$zone
