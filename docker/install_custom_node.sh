#!/bin/bash

set -e

CUSTOM_NODE_PATH="/root/autodl-tmp/ComfyUI/custom_nodes"

PLUGIN_LIST=(
    "https://github.com/billwuhao/ComfyUI_IndexTTS"
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite"
    "https://github.com/chflame163/ComfyUI_LayerStyle"
    "https://github.com/kijai/ComfyUI-KJNodes"
    "https://github.com/kijai/ComfyUI-WanVideoWrapper"
    "https://github.com/yolain/ComfyUI-Easy-Use"
    "https://github.com/melMass/comfy_mtb"
    "https://github.com/pythongosssss/ComfyUI-Custom-Scripts"
    "https://github.com/pollockjj/ComfyUI-MultiGPU"
)

echo "开始安装ComfyUI自定义节点..."

if [ ! -d "$CUSTOM_NODE_PATH" ]; then
    echo "错误：目录 $CUSTOM_NODE_PATH 不存在"
    exit 1
fi

cd "$CUSTOM_NODE_PATH"
echo "进入工作目录: $CUSTOM_NODE_PATH"

for plugin_url in "${PLUGIN_LIST[@]}"; do
    plugin_name=$(basename "$plugin_url" .git)
    
    echo "处理插件: $plugin_name"
    
    if [ -d "$plugin_name" ]; then
        echo "插件 $plugin_name 已存在，跳过安装"
        continue
    fi
    
    echo "正在克隆插件: $plugin_name"
    if git clone --depth=1 "$plugin_url"; then
        echo "成功克隆插件: $plugin_name"
        
        cd "$plugin_name"
        
        if [ -f "requirements.txt" ]; then
            echo "正在安装依赖: $plugin_name"
            if pip install -r requirements.txt; then
                echo "成功安装依赖: $plugin_name"
            else
                echo "警告：安装依赖失败: $plugin_name"
            fi
        else
            echo "插件 $plugin_name 没有requirements.txt文件"
        fi
        
        cd ..
    else
        echo "错误：克隆插件失败: $plugin_name"
        exit 1
    fi
done

echo "所有插件安装完成！"