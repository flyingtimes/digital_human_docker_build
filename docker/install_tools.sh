#!/bin/bash

# 检查是否启用dryrun模式
DRYRUN=false
if [[ "$1" == "dryrun" ]]; then
    DRYRUN=true
    echo "# DRYRUN模式：只输出要执行的命令，不做实际执行"
    echo "# 以下命令可以直接复制到Dockerfile中"
fi

# 执行命令的函数
run_command() {
    if [[ "$DRYRUN" == "true" ]]; then
        echo "# $1"
        echo "RUN $1"
    else
        echo "执行: $1"
        eval "$1"
    fi
}

# 安装系统依赖
run_command "apt-get update && apt-get -y install git-lfs"
run_command "apt-get -y install ffmpeg"

# 升级pip并安装Python包
run_command "python -m pip install --upgrade pip"
run_command "pip install --upgrade transformers==4.51.0"
run_command "pip install huggingface_hub[cli] modelscope deepspeed"

# 切换目录并克隆仓库
run_command "cd /root/autodl-tmp/ && git clone --depth=1 https://github.com/comfyanonymous/ComfyUI"
