#!/usr/bin/env python3
"""
ComfyUI模型下载脚本
支持并发下载，优先使用ModelScope，失败后使用HuggingFace CLI
"""

import os
import subprocess
import concurrent.futures
import sys
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_download.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 工作目录
MODEL_PATH = "/root/autodl-tmp/ComfyUI/models"

# 模型下载列表
MODEL_LIST = [
    # voice repos
    {
        "repo": "funasr/campplus",
        "files": "full",
        "dest": "TTS/campplus",
    },
    {
        "repo": "IndexTeam/IndexTTS-2",
        "files": "full",
        "dest": "TTS/IndexTTS-2"
    },
    {
        "repo": "facebook/w2v-bert-2.0",
        "files": "full",
        "dest": "TTS/w2v-bert-2.0"
    },
    {
        "repo": "amphion/MaskGCT",
        "files": "semantic_codec*",
        "dest": "TTS/MaskGCT"
    },
    {
        "repo": "nvidia/bigvgan_v2_22khz_80band_256x",
        "files": "bigvgan_generator.pt,config.json",
        "dest": "TTS/bigvgan_v2_22khz_80band_256x"
    },
    # video repos
    {
        "repo": "Kijai/WanVideo_comfy",
        "files": "InfiniteTalk/Wan2_1-InfiniTetalk-Single_fp16.safetensors",
        "dest": "diffusion_models/InfiniteTalk"
    },
    {
        "repo": "Kijai/WanVideo_comfy",
        "files": "Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank16_bf16.safetensors",
        "dest": "loras"
    },
    {
        "repo": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
        "files": "split_files/text_encoders/umt5_xxl_fp16.safetensors",
        "dest": "text_encoders"
    },
    {
        "repo": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
        "files": "split_files/vae/wan_2.1_vae.safetensors",
        "dest": "vae"
    },
    {
        "repo": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
        "files": "split_files/clip_vision/clip_vision_h.safetensors",
        "dest": "clip_vision"
    },
    {
        "repo": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
        "files": "split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors",
        "dest": "diffusion_models"
    },
    {
        "repo": "Kijai/wav2vec2_safetensors",
        "files": "wav2vec2-chinese-base_fp16.safetensors",
        "dest": "wav2vec2"
    }
]

def run_command(command: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """执行系统命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=3600  # 1小时超时
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)

def check_directory_exists(path: str) -> bool:
    """检查目录是否存在"""
    return os.path.exists(path) and os.path.isdir(path)

def check_files_exist(dest_path: str, files: str) -> bool:
    """检查文件是否已存在"""
    if not check_directory_exists(dest_path):
        return False
    
    # 检查成功标记文件
    marker_file = os.path.join(dest_path, ".download_success")
    if os.path.exists(marker_file):
        return True
    
    if files == "full":
        # 检查目录是否为空
        return len(os.listdir(dest_path)) > 0
    else:
        # 检查指定文件是否存在
        file_list = [f.strip() for f in files.split(',')]
        for file in file_list:
            file_path = os.path.join(dest_path, file)
            if not os.path.exists(file_path):
                return False
        return True

def uninstall_xnet():
    """卸载xnet"""
    logger.info("Uninstalling xnet...")
    success, output = run_command("pip uninstall xnet -y")
    if success:
        logger.info("xnet uninstalled successfully")
    else:
        logger.warning(f"Failed to uninstall xnet: {output}")

def create_success_marker(dest_path: str) -> None:
    """创建下载成功标记文件"""
    marker_file = os.path.join(dest_path, ".download_success")
    try:
        with open(marker_file, 'w') as f:
            f.write(f"Download completed at {__import__('datetime').datetime.now()}\n")
        logger.info(f"Created success marker at {marker_file}")
    except Exception as e:
        logger.warning(f"Failed to create success marker: {e}")

def download_with_modelscope(repo: str, files: str, dest_path: str, resume: bool = False) -> bool:
    """使用ModelScope下载模型"""
    try:
        os.makedirs(dest_path, exist_ok=True)
        
        if files == "full":
            command = f"modelscope download --model {repo} --local_dir {dest_path}"
        else:
            command = f"modelscope download --model {repo} --include '{files}' --local_dir {dest_path}"
        
        # ModelScope CLI默认支持断点续传，不需要额外参数
        logger.info(f"Downloading {repo} using ModelScope{' (resume)' if resume else ''}...")
        success, output = run_command(command)
        
        if success:
            logger.info(f"Successfully downloaded {repo} using ModelScope")
            create_success_marker(dest_path)
            return True
        else:
            logger.warning(f"ModelScope download failed for {repo}: {output}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {repo} with ModelScope: {e}")
        return False

def download_with_huggingface(repo: str, files: str, dest_path: str, resume: bool = False) -> bool:
    """使用HuggingFace CLI下载模型"""
    try:
        os.makedirs(dest_path, exist_ok=True)
        
        # 设置环境变量
        env_command = "export HF_ENDPOINT=https://hf-mirror.com"
        
        if files == "full":
            file_args = ""
        else:
            file_list = [f.strip() for f in files.split(',')]
            file_args = " ".join(file_list)
        
        resume_flag = "--resume-download" if resume else ""
        command = f"{env_command} && huggingface-cli download {resume_flag} --local-dir {dest_path} {repo} {file_args}"
        
        logger.info(f"Downloading {repo} using HuggingFace CLI{' (resume)' if resume else ''}...")
        success, output = run_command(command)
        
        if success:
            logger.info(f"Successfully downloaded {repo} using HuggingFace CLI")
            create_success_marker(dest_path)
            return True
        else:
            logger.error(f"HuggingFace CLI download failed for {repo}: {output}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {repo} with HuggingFace CLI: {e}")
        return False

def download_model(model_info: Dict) -> bool:
    """下载单个模型"""
    repo = model_info["repo"]
    files = model_info["files"]
    dest = model_info["dest"]
    
    dest_path = os.path.join(MODEL_PATH, dest)
    logger.info(f"Processing model: {repo} -> {dest_path}")
    
    # 检查文件是否已存在
    if check_files_exist(dest_path, files):
        logger.info(f"Model {repo} already exists at {dest_path}, skipping...")
        return True
    
    # 检查是否存在部分下载，决定是否使用resume
    marker_file = os.path.join(dest_path, ".download_success")
    should_resume = os.path.exists(dest_path) and not os.path.exists(marker_file)
    
    # 尝试ModelScope下载
    if download_with_modelscope(repo, files, dest_path, resume=should_resume):
        return True
    
    # ModelScope失败，尝试HuggingFace CLI
    logger.info(f"ModelScope failed for {repo}, trying HuggingFace CLI...")
    if download_with_huggingface(repo, files, dest_path, resume=should_resume):
        return True
    
    logger.error(f"Failed to download {repo} using both methods")
    return False

def main():
    """主函数"""
    logger.info("Starting ComfyUI model download script...")
    logger.info(f"Model path: {MODEL_PATH}")
    
    # 卸载xnet
    uninstall_xnet()
    
    # 确保工作目录存在
    os.makedirs(MODEL_PATH, exist_ok=True)
    
    # 统计信息
    total_models = len(MODEL_LIST)
    successful_downloads = 0
    failed_downloads = 0
    
    # 并发下载
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for model_info in MODEL_LIST:
            future = executor.submit(download_model, model_info)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    successful_downloads += 1
                else:
                    failed_downloads += 1
            except Exception as e:
                logger.error(f"Error in download task: {e}")
                failed_downloads += 1
    
    # 输出统计信息
    logger.info(f"\nDownload Summary:")
    logger.info(f"Total models: {total_models}")
    logger.info(f"Successful downloads: {successful_downloads}")
    logger.info(f"Failed downloads: {failed_downloads}")
    logger.info(f"Success rate: {successful_downloads/total_models*100:.1f}%")
    
    if failed_downloads > 0:
        logger.error(f"Failed to download {failed_downloads} models. Check the log for details.")
        sys.exit(1)
    else:
        logger.info("All models downloaded successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()