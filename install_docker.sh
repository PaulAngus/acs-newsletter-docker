#!/bin/bash
#DOCKER_BUILDKIT=1 docker build --tag=acsn:0.1 . && img=`docker image ls | grep acsn | grep 0.1 | awk '{print $3}'` && docker run -it --entrypoint /bin/bash --env-file ./env.vars $img
DOCKER_BUILDKIT=1 docker build --tag=acsn:0.1 . && img=`docker image ls | grep acsn | grep 0.1 | awk '{print $3}'` && docker run --rm -it --env-file ./env.vars $img
