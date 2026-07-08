#!/usr/bin/env bash

#DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#cd $DIR

#docker build -f $DIR/Dockerfile -t orca4:latest ..

docker stop cosma_auv_sim
docker container remove cosma_auv_sim
docker image remove cosma_auv_sim


docker build -t cosma_auv_sim:latest .