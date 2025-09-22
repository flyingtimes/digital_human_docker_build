#!/bin/bash

set -e

CUSTOM_NODE_PATH="/root/autodl-tmp/ComfyUI/custom_nodes"

DRYRUN=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dryrun|-d)
            DRYRUN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "使用方法: $0 [--dryrun|-d]"
            exit 1
            ;;
    esac
done

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

if [ "$DRYRUN" = false ]; then
    echo "开始安装ComfyUI自定义节点..."
fi

if [ "$DRYRUN" = true ]; then
    echo "cd \"$CUSTOM_NODE_PATH\""
else
    cd "$CUSTOM_NODE_PATH"
fi

for plugin_url in "${PLUGIN_LIST[@]}"; do
    plugin_name=$(basename "$plugin_url" .git)
    
    if [ "$DRYRUN" = true ]; then
        echo "git clone --depth=1 \"$plugin_url\""
        echo "cd \"$plugin_name\""
        echo "pip install -r requirements.txt"
        echo "cd .."
    else
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
    fi
done

if [ "$DRYRUN" = false ]; then
    echo "所有插件安装完成！"
fi