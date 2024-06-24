#!/bin/bash

CONTAINER_NAME=deepstream_docker
export DISPLAY=:0
xhost +local:docker

# Re-use existing container.
if [ "$(docker ps -a --quiet --filter status=running --filter name=$CONTAINER_NAME)" ]; then
    docker exec -i -t -u admin --workdir /workspaces $CONTAINER_NAME /bin/bash $@
    exit 0
fi

docker run -it --rm --network host \
-v /dev/*:/dev/* \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v /tmp/argus_socket:/tmp/argus_socket \
-v /tmp/nvscsock:/tmp/nvscsock \
-v /tmp/camsock:/tmp/camsock \
-v ./workspace:/workspace \
-e DISPLAY=:0 \
-e NVIDIA_VISIBLE_DEVICES=all \
--privileged \
--runtime nvidia \
--name $CONTAINER_NAME \
--workdir /workspace \
tlln/tds_docker:1.0 \
python main.py $1


