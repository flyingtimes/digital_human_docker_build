#!/bin/bash
apt-get update && apt-get -y install git-lfs
apt-get -y install ffmpeg
python -m pip install --upgrade pip
pip install --upgrade transformers==4.51.0
pip install huggingface_hub[cli] modelscope deepspeed
