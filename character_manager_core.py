"""
数字人角色管理器 - 核心功能实现
"""

import os
import time
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
import logging

from character_models import (
    CharacterInfo, ValidationResult, CharacterError, 
    CharacterNotFoundError, CharacterValidationError,
    CharacterFileError, is_valid_audio_file, 
    is_valid_image_file, is_valid_video_file,
    sanitize_character_name, get_file_size_mb
)


@dataclass
class CacheEntry:
    """缓存条目"""
    character_info: CharacterInfo
    timestamp: float
    ttl: float = 300.0  # 5分钟缓存时间
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.timestamp > self.ttl


class CharacterManager:
    """数字人角色管理器"""
    
    def __init__(self, characters_dir: str = "characters"):
        self.characters_dir = characters_dir
        self.characters: Dict[str, CharacterInfo] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self.supported_audio_formats = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm'}
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 确保角色目录存在
        self._ensure_characters_dir()
    
    def _ensure_characters_dir(self):
        """确保角色目录存在"""
        if not os.path.exists(self.characters_dir):
            try:
                os.makedirs(self.characters_dir)
                self.logger.info(f"创建角色目录: {self.characters_dir}")
            except OSError as e:
                raise CharacterError(f"无法创建角色目录 '{self.characters_dir}': {e}")
    
    def _get_cache_key(self, character_name: str) -> str:
        """获取缓存键"""
        return f"{character_name}_{os.path.getmtime(self.characters_dir) if os.path.exists(self.characters_dir) else 0}"
    
    def _cache_character(self, character_info: CharacterInfo):
        """缓存角色信息"""
        cache_key = self._get_cache_key(character_info.name)
        self.cache[cache_key] = CacheEntry(character_info, time.time())
    
    def _get_cached_character(self, character_name: str) -> Optional[CharacterInfo]:
        """从缓存获取角色信息"""
        cache_key = self._get_cache_key(character_name)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                return entry.character_info
            else:
                del self.cache[cache_key]
        return None
    
    def _sanitize_path(self, path: str) -> str:
        """清理路径，防止路径遍历攻击"""
        try:
            # 规范化路径
            normalized = os.path.normpath(path)
            # 转换为绝对路径
            abs_path = os.path.abspath(normalized)
            # 确保在项目目录内
            characters_abs = os.path.abspath(self.characters_dir)
            if not abs_path.startswith(characters_abs):
                raise CharacterError(f"路径越界: {path}")
            return abs_path
        except (OSError, ValueError) as e:
            raise CharacterError(f"无效路径: {path} - {e}")
    
    def _find_files_by_type(self, directory: str, extensions: Set[str]) -> List[str]:
        """在目录中查找指定扩展名的文件"""
        if not os.path.exists(directory):
            return []
        
        found_files = []
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in extensions:
                            found_files.append(entry.path)
        except OSError as e:
            self.logger.warning(f"扫描目录失败: {directory} - {e}")
        
        return sorted(found_files)
    
    def _select_best_file(self, files: List[str]) -> Optional[str]:
        """选择最佳文件（优先选择第一个文件）"""
        if not files:
            return None
        
        # 简单策略：返回第一个文件
        # 可以扩展为基于文件大小、修改时间等更复杂的策略
        return files[0]
    
    def validate_character(self, character_name: str) -> ValidationResult:
        """验证角色文件夹的完整性"""
        # 清理角色名称
        safe_name = sanitize_character_name(character_name)
        if safe_name != character_name:
            self.logger.warning(f"角色名称被清理: '{character_name}' -> '{safe_name}'")
        
        result = ValidationResult(safe_name)
        
        # 检查角色文件夹是否存在
        character_dir = self._sanitize_path(os.path.join(self.characters_dir, safe_name))
        if not os.path.exists(character_dir):
            result.add_error("角色文件夹不存在")
            return result
        
        # 检查是否为目录
        if not os.path.isdir(character_dir):
            result.add_error("角色路径不是目录")
            return result
        
        # 查找音频文件
        audio_files = self._find_files_by_type(character_dir, self.supported_audio_formats)
        if not audio_files:
            result.add_error("缺少参考音频文件")
        else:
            for audio_file in audio_files:
                result.add_found_file('audio', audio_file)
                file_size = get_file_size_mb(audio_file)
                if file_size > 50:  # 50MB
                    result.add_warning(f"音频文件较大: {file_size:.1f}MB")
        
        # 查找图片文件
        image_files = self._find_files_by_type(character_dir, self.supported_image_formats)
        for image_file in image_files:
            result.add_found_file('images', image_file)
            file_size = get_file_size_mb(image_file)
            if file_size > 10:  # 10MB
                result.add_warning(f"图片文件较大: {file_size:.1f}MB")
        
        # 查找视频文件
        video_files = self._find_files_by_type(character_dir, self.supported_video_formats)
        for video_file in video_files:
            result.add_found_file('videos', video_file)
            file_size = get_file_size_mb(video_file)
            if file_size > 100:  # 100MB
                result.add_warning(f"视频文件较大: {file_size:.1f}MB")
        
        # 检查是否至少有一个视觉文件
        if not result.has_visual():
            result.add_error("缺少参考图像或视频文件")
        
        # 检查配置文件
        config_path = os.path.join(character_dir, "config.json")
        if os.path.exists(config_path):
            try:
                from character_models import CharacterConfig
                config = CharacterConfig.load_config(character_dir)
                if config:
                    result.add_warning("发现配置文件，将被使用")
            except CharacterFileError as e:
                result.add_warning(f"配置文件加载失败: {e}")
        
        return result
    
    def load_character(self, character_name: str) -> CharacterInfo:
        """加载指定角色的信息"""
        # 检查缓存
        cached = self._get_cached_character(character_name)
        if cached:
            return cached
        
        # 清理角色名称
        safe_name = sanitize_character_name(character_name)
        
        # 验证角色
        validation_result = self.validate_character(safe_name)
        if not validation_result.is_valid:
            raise CharacterValidationError(safe_name, validation_result.errors)
        
        # 获取角色目录
        character_dir = self._sanitize_path(os.path.join(self.characters_dir, safe_name))
        
        # 选择最佳音频文件
        audio_files = validation_result.found_files['audio']
        if not audio_files:
            raise CharacterValidationError(safe_name, ["缺少参考音频文件"])
        audio_path = self._select_best_file(audio_files)
        
        # 选择最佳视觉文件
        visual_path = None
        visual_type = None
        
        # 优先选择图片
        image_files = validation_result.found_files['images']
        if image_files:
            visual_path = self._select_best_file(image_files)
            visual_type = 'image'
        else:
            # 其次选择视频
            video_files = validation_result.found_files['videos']
            if video_files:
                visual_path = self._select_best_file(video_files)
                visual_type = 'video'
        
        if not visual_path:
            raise CharacterValidationError(safe_name, ["缺少参考图像或视频文件"])
        
        # 加载配置
        try:
            from character_models import CharacterConfig
            config = CharacterConfig.load_config(character_dir)
        except CharacterFileError:
            config = {}
        
        # 创建角色信息
        character_info = CharacterInfo(
            name=safe_name,
            audio_path=audio_path,
            visual_path=visual_path,
            visual_type=visual_type,
            config=config,
            character_dir=character_dir,
            validation_result=validation_result
        )
        
        # 缓存角色信息
        self._cache_character(character_info)
        
        return character_info
    
    def scan_characters(self) -> Dict[str, CharacterInfo]:
        """扫描characters目录，返回所有有效角色"""
        if not os.path.exists(self.characters_dir):
            self.logger.warning(f"角色目录不存在: {self.characters_dir}")
            return {}
        
        characters = {}
        
        try:
            with os.scandir(self.characters_dir) as entries:
                for entry in entries:
                    if entry.is_dir():
                        character_name = entry.name
                        try:
                            # 跳过隐藏目录
                            if character_name.startswith('.'):
                                continue
                            
                            # 尝试加载角色
                            character_info = self.load_character(character_name)
                            characters[character_name] = character_info
                            self.logger.info(f"加载角色: {character_name}")
                            
                        except CharacterValidationError as e:
                            self.logger.warning(f"角色验证失败: {character_name} - {e.errors}")
                        except Exception as e:
                            self.logger.error(f"加载角色失败: {character_name} - {e}")
        
        except OSError as e:
            self.logger.error(f"扫描角色目录失败: {e}")
        
        self.characters = characters
        return characters
    
    def list_characters(self) -> List[str]:
        """列出所有可用角色名称"""
        if not self.characters:
            self.scan_characters()
        return list(self.characters.keys())
    
    def get_character_info(self, character_name: str) -> Optional[CharacterInfo]:
        """获取角色信息，如果不存在返回None"""
        try:
            return self.load_character(character_name)
        except CharacterError:
            return None
    
    def character_exists(self, character_name: str) -> bool:
        """检查角色是否存在"""
        result = self.validate_character(character_name)
        return result.is_valid
    
    def get_character_summary(self, character_name: str) -> Optional[str]:
        """获取角色摘要信息"""
        try:
            character_info = self.load_character(character_name)
            validation_result = character_info.validation_result
            
            if validation_result:
                return validation_result.get_detailed_summary()
            else:
                return f"角色 '{character_name}' 基本信息:\n" \
                       f"  音频: {Path(character_info.audio_path).name}\n" \
                       f"  视觉: {Path(character_info.visual_path).name} ({character_info.visual_type})"
        
        except CharacterError as e:
            return f"无法获取角色信息: {e}"
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        self.logger.info("角色缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        active_entries = total_entries - expired_entries
        
        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': expired_entries
        }