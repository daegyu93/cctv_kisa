FROM nvcr.io/nvidia/deepstream-l4t:6.3-samples

RUN apt update

RUN apt install -y python3-gi python3-dev python3-gst-1.0 python-gi-dev git \
    python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev \
    libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev \
    libgstreamer-plugins-base1.0-dev \
    python3-numpy \
    && pip install opencv-python pandas xmltodict \
    && cd /opt/nvidia/deepstream/deepstream/sources/ \
    && git clone -b v1.1.8 https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git \
    && cd deepstream_python_apps/ \
    && git submodule update --init \
    && apt-get install -y apt-transport-https ca-certificates -y \
    && update-ca-certificates \
    && cd /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/3rdparty/gst-python/ \
    && ./autogen.sh \
    && make \
    && make install \
    && cd /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings \
    && mkdir build \
    && cd build \
    && wget https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.8/pyds-1.1.8-py3-none-linux_aarch64.whl \
    && pip3 install ./pyds-1.1.8-py3-none-linux_aarch64.whl
