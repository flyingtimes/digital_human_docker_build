"""
数字人角色管理模块 - 数据模型和异常类
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import json


class CharacterError(Exception):
    """角色相关错误基类"""
    pass


class CharacterNotFoundError(CharacterError):
    """角色不存在错误"""
    def __init__(self, character_name: str):
        self.character_name = character_name
        super().__init__(f"角色 '{character_name}' 不存在")


class CharacterValidationError(CharacterError):
    """角色验证失败错误"""
    def __init__(self, character_name: str, errors: List[str]):
        self.character_name = character_name
        self.errors = errors
        error_msg = f"角色 '{character_name}' 验证失败: " + "; ".join(errors)
        super().__init__(error_msg)


class CharacterFileError(CharacterError):
    """角色文件相关错误"""
    def __init__(self, character_name: str, file_path: str, reason: str):
        self.character_name = character_name
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"角色 '{character_name}' 文件错误: {file_path} - {reason}")


@dataclass
class CharacterInfo:
    """数字人角色信息"""
    name: str
    audio_path: str
    visual_path: str
    visual_type: str  # 'image' 或 'video'
    config: Dict[str, Any] = field(default_factory=dict)
    character_dir: str = ""
    validation_result: Optional['ValidationResult'] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.character_dir and self.audio_path:
            self.character_dir = str(Path(self.audio_path).parent)
    
    def get_positive_prompt(self, default: str = "A person talking") -> str:
        """获取正面提示词"""
        return self.config.get('positive_prompt', default)
    
    def get_negative_prompt(self, default: str = "") -> str:
        """获取负面提示词"""
        return self.config.get('negative_prompt', default)
    
    def get_workflow_params(self) -> Dict[str, Any]:
        """获取工作流参数"""
        return self.config.get('workflow_params', {})


@dataclass
class ValidationResult:
    """角色验证结果"""
    character_name: str
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    found_files: Dict[str, List[str]] = field(default_factory=lambda: {
        'audio': [],
        'images': [],
        'videos': []
    })
    
    def add_error(self, message: str):
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """添加警告信息"""
        self.warnings.append(message)
    
    def add_found_file(self, file_type: str, file_path: str):
        """添加找到的文件"""
        if file_type in self.found_files:
            self.found_files[file_type].append(file_path)
    
    def has_audio(self) -> bool:
        """是否有音频文件"""
        return len(self.found_files['audio']) > 0
    
    def has_visual(self) -> bool:
        """是否有视觉文件（图片或视频）"""
        return len(self.found_files['images']) > 0 or len(self.found_files['videos']) > 0
    
    def has_images(self) -> bool:
        """是否有图片文件"""
        return len(self.found_files['images']) > 0
    
    def has_videos(self) -> bool:
        """是否有视频文件"""
        return len(self.found_files['videos']) > 0
    
    def get_summary(self) -> str:
        """获取验证结果摘要"""
        if self.is_valid:
            return f"✅ 角色 '{self.character_name}' 验证通过"
        else:
            return f"❌ 角色 '{self.character_name}' 验证失败: {len(self.errors)} 个错误"
    
    def get_detailed_summary(self) -> str:
        """获取详细的验证结果摘要"""
        lines = [self.get_summary()]
        
        if self.errors:
            lines.append("错误:")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append("警告:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        lines.append("找到的文件:")
        for file_type, files in self.found_files.items():
            if files:
                lines.append(f"  {file_type}: {len(files)} 个")
                for file in files[:3]:  # 只显示前3个文件
                    lines.append(f"    - {Path(file).name}")
                if len(files) > 3:
                    lines.append(f"    ... 还有 {len(files) - 3} 个文件")
        
        return "\n".join(lines)


class CharacterConfig:
    """角色配置管理"""
    
    @staticmethod
    def load_config(character_dir: str) -> Dict[str, Any]:
        """加载角色配置文件"""
        config_path = os.path.join(character_dir, "config.json")
        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise CharacterFileError(
                Path(character_dir).name, 
                config_path, 
                f"配置文件加载失败: {e}"
            )
    
    @staticmethod
    def save_config(character_dir: str, config: Dict[str, Any]):
        """保存角色配置文件"""
        config_path = os.path.join(character_dir, "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise CharacterFileError(
                Path(character_dir).name, 
                config_path, 
                f"配置文件保存失败: {e}"
            )
    
    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "positive_prompt": "A person talking naturally",
            "negative_prompt": "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background",
            "workflow_params": {
                "temperature": 0.8,
                "top_k": 30,
                "top_p": 0.8,
                "num_beams": 3
            },
            "description": "",
            "tags": []
        }


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小（MB）"""
    if not os.path.exists(file_path):
        return 0.0
    return os.path.getsize(file_path) / (1024 * 1024)


def is_valid_audio_file(file_path: str) -> bool:
    """检查是否为有效的音频文件"""
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
    return os.path.splitext(file_path)[1].lower() in audio_extensions


def is_valid_image_file(file_path: str) -> bool:
    """检查是否为有效的图片文件"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
    return os.path.splitext(file_path)[1].lower() in image_extensions


def is_valid_video_file(file_path: str) -> bool:
    """检查是否为有效的视频文件"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm'}
    return os.path.splitext(file_path)[1].lower() in video_extensions


def sanitize_character_name(name: str) -> str:
    """清理角色名称，移除不安全字符"""
    # 移除路径分隔符和其他危险字符
    unsafe_chars = {'/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0'}
    sanitized = name
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 移除开头和结尾的空格和点
    sanitized = sanitized.strip(' .')
    
    # 确保不为空
    if not sanitized:
        sanitized = "unnamed_character"
    
    return sanitized