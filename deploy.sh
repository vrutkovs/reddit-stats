#!/bin/bash

set -eux

sudo docker build -t gcr.io/reddit-stats-153800/reddit-stats . --no-cache
sudo ~/bin/google-cloud-sdk/bin/gcloud docker -- push gcr.io/reddit-stats-153800/reddit-stats
kubectl rolling-update reddit-stats --image=gcr.io/reddit-stats-153800/reddit-stats --image-pull-policy=Always
