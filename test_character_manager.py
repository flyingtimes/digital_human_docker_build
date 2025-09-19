"""
数字人角色管理器 - 单元测试
"""

import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from character_models import (
    CharacterInfo, ValidationResult, CharacterError,
    CharacterNotFoundError, CharacterValidationError,
    CharacterFileError, CharacterConfig,
    is_valid_audio_file, is_valid_image_file, is_valid_video_file,
    sanitize_character_name, get_file_size_mb
)

from character_manager_core import CharacterManager, CacheEntry


class TestCharacterModels(unittest.TestCase):
    """测试数据模型和工具函数"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio = os.path.join(self.temp_dir, "test.mp3")
        self.test_image = os.path.join(self.temp_dir, "test.jpg")
        
        # 创建测试文件
        with open(self.test_audio, 'w') as f:
            f.write("test audio content")
        with open(self.test_image, 'w') as f:
            f.write("test image content")
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_character_info_creation(self):
        """测试角色信息创建"""
        character = CharacterInfo(
            name="test_char",
            audio_path=self.test_audio,
            visual_path=self.test_image,
            visual_type="image"
        )
        
        self.assertEqual(character.name, "test_char")
        self.assertEqual(character.audio_path, self.test_audio)
        self.assertEqual(character.visual_path, self.test_image)
        self.assertEqual(character.visual_type, "image")
        self.assertEqual(character.config, {})
        self.assertTrue(character.character_dir.endswith(self.temp_dir))
    
    def test_character_info_prompts(self):
        """测试角色提示词获取"""
        config = {
            "positive_prompt": "A woman talking",
            "negative_prompt": "bad quality"
        }
        
        character = CharacterInfo(
            name="test_char",
            audio_path=self.test_audio,
            visual_path=self.test_image,
            visual_type="image",
            config=config
        )
        
        self.assertEqual(character.get_positive_prompt(), "A woman talking")
        self.assertEqual(character.get_negative_prompt(), "bad quality")
        
        # 测试默认值
        character.config = {}
        self.assertEqual(character.get_positive_prompt(), "A person talking")
        self.assertEqual(character.get_negative_prompt(), "")
    
    def test_validation_result(self):
        """测试验证结果"""
        result = ValidationResult("test_char")
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        
        # 添加错误
        result.add_error("测试错误")
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        
        # 添加警告
        result.add_warning("测试警告")
        self.assertEqual(len(result.warnings), 1)
        
        # 添加找到的文件
        result.add_found_file('audio', self.test_audio)
        result.add_found_file('images', self.test_image)
        
        self.assertTrue(result.has_audio())
        self.assertTrue(result.has_visual())
        self.assertTrue(result.has_images())
        self.assertFalse(result.has_videos())
    
    def test_validation_result_summary(self):
        """测试验证结果摘要"""
        result = ValidationResult("test_char")
        summary = result.get_summary()
        self.assertIn("test_char", summary)
        self.assertIn("验证通过", summary)
        
        # 添加错误
        result.add_error("测试错误")
        summary = result.get_summary()
        self.assertIn("验证失败", summary)
    
    def test_character_config(self):
        """测试角色配置"""
        config_data = {
            "positive_prompt": "test positive",
            "description": "test character"
        }
        
        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # 测试加载配置
        loaded_config = CharacterConfig.load_config(self.temp_dir)
        self.assertEqual(loaded_config["positive_prompt"], "test positive")
        
        # 测试默认配置
        default_config = CharacterConfig.create_default_config()
        self.assertIn("positive_prompt", default_config)
        self.assertIn("negative_prompt", default_config)
        self.assertIn("workflow_params", default_config)
    
    def test_file_validation_functions(self):
        """测试文件验证函数"""
        self.assertTrue(is_valid_audio_file("test.mp3"))
        self.assertTrue(is_valid_audio_file("test.wav"))
        self.assertFalse(is_valid_audio_file("test.txt"))
        
        self.assertTrue(is_valid_image_file("test.jpg"))
        self.assertTrue(is_valid_image_file("test.png"))
        self.assertFalse(is_valid_image_file("test.txt"))
        
        self.assertTrue(is_valid_video_file("test.mp4"))
        self.assertTrue(is_valid_video_file("test.avi"))
        self.assertFalse(is_valid_video_file("test.txt"))
    
    def test_sanitize_character_name(self):
        """测试角色名称清理"""
        self.assertEqual(sanitize_character_name("test/char"), "test_char")
        self.assertEqual(sanitize_character_name("test\\char"), "test_char")
        self.assertEqual(sanitize_character_name("  test  "), "test")
        self.assertEqual(sanitize_character_name(""), "unnamed_character")
        self.assertEqual(sanitize_character_name("..."), "unnamed_character")
    
    def test_get_file_size_mb(self):
        """测试文件大小获取"""
        # 创建一个已知大小的文件
        test_file = os.path.join(self.temp_dir, "size_test.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 1024)  # 1KB
        
        size_mb = get_file_size_mb(test_file)
        self.assertAlmostEqual(size_mb, 1024 / (1024 * 1024), places=6)
        
        # 测试不存在的文件
        size_mb = get_file_size_mb("nonexistent.txt")
        self.assertEqual(size_mb, 0.0)


class TestCharacterManager(unittest.TestCase):
    """测试角色管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.characters_dir = os.path.join(self.temp_dir, "characters")
        self.manager = CharacterManager(self.characters_dir)
        
        # 创建测试角色
        self.test_character_dir = os.path.join(self.characters_dir, "test_char")
        os.makedirs(self.test_character_dir, exist_ok=True)
        
        # 创建测试文件
        self.test_audio = os.path.join(self.test_character_dir, "test.mp3")
        self.test_image = os.path.join(self.test_character_dir, "test.jpg")
        
        with open(self.test_audio, 'w') as f:
            f.write("test audio content")
        with open(self.test_image, 'w') as f:
            f.write("test image content")
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_characters_dir(self):
        """测试确保角色目录存在"""
        # 删除目录
        if os.path.exists(self.characters_dir):
            shutil.rmtree(self.characters_dir)
        
        # 重新创建管理器
        manager = CharacterManager(self.characters_dir)
        self.assertTrue(os.path.exists(self.characters_dir))
    
    def test_validate_character_success(self):
        """测试角色验证成功"""
        result = self.manager.validate_character("test_char")
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertTrue(result.has_audio())
        self.assertTrue(result.has_images())
        self.assertIn(self.test_audio, result.found_files['audio'])
        self.assertIn(self.test_image, result.found_files['images'])
    
    def test_validate_character_not_found(self):
        """测试角色不存在"""
        result = self.manager.validate_character("nonexistent")
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("不存在", result.errors[0])
    
    def test_validate_character_missing_files(self):
        """测试角色缺少文件"""
        # 删除文件
        os.remove(self.test_audio)
        os.remove(self.test_image)
        
        result = self.manager.validate_character("test_char")
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertFalse(result.has_audio())
        self.assertFalse(result.has_visual())
    
    def test_load_character_success(self):
        """测试加载角色成功"""
        character = self.manager.load_character("test_char")
        
        self.assertEqual(character.name, "test_char")
        self.assertEqual(character.audio_path, self.test_audio)
        self.assertEqual(character.visual_path, self.test_image)
        self.assertEqual(character.visual_type, "image")
    
    def test_load_character_not_found(self):
        """测试加载不存在的角色"""
        with self.assertRaises(CharacterValidationError):
            self.manager.load_character("nonexistent")
    
    def test_scan_characters(self):
        """测试扫描角色"""
        characters = self.manager.scan_characters()
        
        self.assertIn("test_char", characters)
        self.assertEqual(len(characters), 1)
        
        character = characters["test_char"]
        self.assertEqual(character.name, "test_char")
    
    def test_list_characters(self):
        """测试列出角色"""
        characters = self.manager.list_characters()
        
        self.assertIn("test_char", characters)
        self.assertEqual(len(characters), 1)
    
    def test_get_character_info(self):
        """测试获取角色信息"""
        character = self.manager.get_character_info("test_char")
        
        self.assertIsNotNone(character)
        self.assertEqual(character.name, "test_char")
        
        # 测试不存在的角色
        character = self.manager.get_character_info("nonexistent")
        self.assertIsNone(character)
    
    def test_character_exists(self):
        """测试检查角色是否存在"""
        self.assertTrue(self.manager.character_exists("test_char"))
    
    def test_get_character_summary(self):
        """测试获取角色摘要"""
        summary = self.manager.get_character_summary("test_char")
        
        self.assertIn("test_char", summary)
        self.assertIn("test.mp3", summary)
        self.assertIn("test.jpg", summary)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次加载
        character1 = self.manager.load_character("test_char")
        
        # 第二次加载应该从缓存获取
        character2 = self.manager.load_character("test_char")
        
        # 应该是同一个对象（缓存命中）
        self.assertIs(character1, character2)
        
        # 清除缓存
        self.manager.clear_cache()
        
        # 再次加载应该重新创建
        character3 = self.manager.load_character("test_char")
        self.assertIsNot(character1, character3)
    
    def test_cache_stats(self):
        """测试缓存统计"""
        # 加载角色以填充缓存
        self.manager.load_character("test_char")
        
        stats = self.manager.get_cache_stats()
        
        self.assertGreaterEqual(stats['total_entries'], 0)
        self.assertGreaterEqual(stats['active_entries'], 0)
        self.assertGreaterEqual(stats['expired_entries'], 0)
    
    def test_sanitize_path_security(self):
        """测试路径安全性"""
        # 测试路径遍历攻击
        with self.assertRaises(CharacterError):
            self.manager._sanitize_path("../../../etc/passwd")
        
        with self.assertRaises(CharacterError):
            self.manager._sanitize_path("..\\..\\windows\\system32")
    
    def test_find_files_by_type(self):
        """测试按类型查找文件"""
        # 在测试目录中查找音频文件
        audio_files = self.manager._find_files_by_type(
            self.test_character_dir, 
            {'.mp3', '.wav'}
        )
        
        self.assertIn(self.test_audio, audio_files)
        self.assertEqual(len(audio_files), 1)
        
        # 查找不存在的文件类型
        txt_files = self.manager._find_files_by_type(
            self.test_character_dir,
            {'.txt'}
        )
        
        self.assertEqual(len(txt_files), 0)


class TestCacheEntry(unittest.TestCase):
    """测试缓存条目"""
    
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        import time
        character = Mock(spec=CharacterInfo)
        entry = CacheEntry(character, time.time())
        
        self.assertEqual(entry.character_info, character)
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiration(self):
        """测试缓存条目过期"""
        import time
        character = Mock(spec=CharacterInfo)
        old_time = time.time() - 400  # 400秒前
        entry = CacheEntry(character, old_time, ttl=300)  # 5分钟TTL
        
        self.assertTrue(entry.is_expired())
    
    def test_cache_entry_not_expired(self):
        """测试缓存条目未过期"""
        import time
        character = Mock(spec=CharacterInfo)
        recent_time = time.time() - 60  # 60秒前
        entry = CacheEntry(character, recent_time, ttl=300)  # 5分钟TTL
        
        self.assertFalse(entry.is_expired())


if __name__ == '__main__':
    unittest.main()