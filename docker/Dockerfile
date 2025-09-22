# 基于pytorch/pytorch:2.8.0-cuda12.6-cudnn9-devel镜像
FROM pytorch/pytorch:2.8.0-cuda12.6-cudnn9-devel

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get -y install git-lfs ffmpeg curl

# 安被uv包管理器
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 安袮Python基础包
RUN uv pip install --system --upgrade transformers==4.51.0 huggingface_hub[cli] modelscope deepspeed

# 创建ComfyUI工作目录
RUN mkdir -p /root/autodl-tmp

# 克隆ComfyUI主仓库
RUN cd /root/autodl-tmp && git clone --depth=1 https://github.com/comfyanonymous/ComfyUI

# 设置工作目录为ComfyUI
WORKDIR /root/autodl-tmp/ComfyUI

# 安装ComfyUI依赖
RUN uv pip install -r requirements.txt

# 创建custom_nodes目录
RUN mkdir -p custom_nodes

# 克隆所有custom_nodes并安装依赖
RUN cd custom_nodes && \
    git clone --depth=1 "https://github.com/billwuhao/ComfyUI_IndexTTS" && \
    cd ComfyUI_IndexTTS && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite" && \
    cd ComfyUI-VideoHelperSuite && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/chflame163/ComfyUI_LayerStyle" && \
    cd ComfyUI_LayerStyle && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/kijai/ComfyUI-KJNodes" && \
    cd ComfyUI-KJNodes && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/kijai/ComfyUI-WanVideoWrapper" && \
    cd ComfyUI-WanVideoWrapper && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/yolain/ComfyUI-Easy-Use" && \
    cd ComfyUI-Easy-Use && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/melMass/comfy_mtb" && \
    cd comfy_mtb && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/pythongosssss/ComfyUI-Custom-Scripts" && \
    cd ComfyUI-Custom-Scripts && uv pip install -r requirements.txt && \
    cd .. && \
    git clone --depth=1 "https://github.com/pollockjj/ComfyUI-MultiGPU" && \
    cd ComfyUI-MultiGPU && uv pip install -r requirements.txt

# 设置环境变量
ENV PYTHONPATH="/root/autodl-tmp/ComfyUI:$PYTHONPATH"

# 暴露端口（如果需要）
EXPOSE 3000

# 设置启动命令
CMD ["python", "/root/autodl-tmp/ComfyUI/main.py", "--listen", "0.0.0.0", "--port", "3000"]