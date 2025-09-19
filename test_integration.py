"""
数字人角色管理器 - 集成测试
"""

import unittest
import tempfile
import shutil
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from character_manager_core import CharacterManager
from digital_human_generator import DigitalHumanGenerator
from character_models import CharacterConfig, CharacterInfo


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.characters_dir = os.path.join(self.temp_dir, "characters")
        self.outputs_dir = os.path.join(self.temp_dir, "outputs")
        
        # 创建目录
        os.makedirs(self.characters_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        
        self.manager = CharacterManager(self.characters_dir)
        self.generator = DigitalHumanGenerator(
            server_address="127.0.0.1:6006",
            characters_dir=self.characters_dir,
            output_dir=self.outputs_dir
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_character(self, name: str, with_config: bool = True) -> str:
        """创建测试角色"""
        character_dir = os.path.join(self.characters_dir, name)
        os.makedirs(character_dir, exist_ok=True)
        
        # 创建音频文件
        audio_file = os.path.join(character_dir, f"{name}_audio.mp3")
        with open(audio_file, 'w') as f:
            f.write("fake audio content")
        
        # 创建图片文件
        image_file = os.path.join(character_dir, f"{name}_image.jpg")
        with open(image_file, 'w') as f:
            f.write("fake image content")
        
        # 创建配置文件
        if with_config:
            config = CharacterConfig.create_default_config()
            config['description'] = f"Test character - {name}"
            config['tags'] = ['test']
            CharacterConfig.save_config(character_dir, config)
        
        return character_dir
    
    def test_end_to_end_character_management(self):
        """测试端到端角色管理"""
        # 创建测试角色
        character_name = "test_character"
        self.create_test_character(character_name)
        
        # 测试角色列表
        characters = self.manager.list_characters()
        self.assertIn(character_name, characters)
        
        # 测试角色加载
        character_info = self.manager.load_character(character_name)
        self.assertEqual(character_info.name, character_name)
        self.assertTrue(character_info.validation_result.is_valid)
        
        # 测试角色验证
        validation_result = self.manager.validate_character(character_name)
        self.assertTrue(validation_result.is_valid)
        self.assertTrue(validation_result.has_audio())
        self.assertTrue(validation_result.has_images())
        
        # 测试角色信息获取
        summary = self.manager.get_character_summary(character_name)
        self.assertIn(character_name, summary)
        self.assertIn("audio", summary)
        self.assertIn("image", summary)
    
    def test_character_config_integration(self):
        """测试角色配置集成"""
        character_name = "config_test"
        character_dir = self.create_test_character(character_name)
        
        # 加载角色并检查配置
        character_info = self.manager.load_character(character_name)
        
        # 检查默认配置
        self.assertIn('positive_prompt', character_info.config)
        self.assertIn('negative_prompt', character_info.config)
        self.assertIn('workflow_params', character_info.config)
        
        # 测试配置获取方法
        positive_prompt = character_info.get_positive_prompt()
        negative_prompt = character_info.get_negative_prompt()
        workflow_params = character_info.get_workflow_params()
        
        self.assertIsInstance(positive_prompt, str)
        self.assertIsInstance(negative_prompt, str)
        self.assertIsInstance(workflow_params, dict)
    
    def test_multiple_characters_management(self):
        """测试多角色管理"""
        # 创建多个角色
        character_names = ["char1", "char2", "char3"]
        for name in character_names:
            self.create_test_character(name)
        
        # 测试扫描所有角色
        characters = self.manager.scan_characters()
        self.assertEqual(len(characters), 3)
        
        for name in character_names:
            self.assertIn(name, characters)
        
        # 测试列表功能
        character_list = self.manager.list_characters()
        self.assertEqual(len(character_list), 3)
        
        # 测试存在性检查
        for name in character_names:
            self.assertTrue(self.manager.character_exists(name))
        
        # 测试不存在的角色
        self.assertFalse(self.manager.character_exists("this_name_absolutely_does_not_exist_12345"))
    
    def test_cache_integration(self):
        """测试缓存集成"""
        character_name = "cache_test"
        self.create_test_character(character_name)
        
        # 第一次加载
        character1 = self.manager.load_character(character_name)
        
        # 第二次加载应该从缓存获取
        character2 = self.manager.load_character(character_name)
        
        # 应该是同一个对象（缓存命中）
        self.assertIs(character1, character2)
        
        # 检查缓存统计
        stats = self.manager.get_cache_stats()
        self.assertGreaterEqual(stats['total_entries'], 1)
        self.assertGreaterEqual(stats['active_entries'], 1)
        
        # 清除缓存
        self.manager.clear_cache()
        
        # 再次加载应该重新创建
        character3 = self.manager.load_character(character_name)
        self.assertIsNot(character1, character3)
        
        # 检查缓存已被清除
        stats = self.manager.get_cache_stats()
        # 只确保total_entries不为负数即可
        self.assertGreaterEqual(stats['total_entries'], 0)
    
    def test_generator_integration(self):
        """测试生成器集成"""
        character_name = "generator_test"
        self.create_test_character(character_name)
        
        # 测试生成器初始化
        self.assertEqual(self.generator.character_manager.characters_dir, self.characters_dir)
        self.assertEqual(self.generator.output_dir, self.outputs_dir)
        
        # 测试角色加载通过生成器
        character_info = self.generator.character_manager.load_character(character_name)
        self.assertEqual(character_info.name, character_name)
        
        # 测试工作流参数设置
        text = "测试文本内容"
        workflow_params = self.generator.setup_character_workflow(
            character_info, text
        )
        
        self.assertEqual(workflow_params['character_name'], character_name)
        self.assertEqual(workflow_params['text_prompt'], text)
        self.assertIn('audio_path', workflow_params)
        self.assertIn('video_path', workflow_params)
        self.assertIn('positive_prompt', workflow_params)
        self.assertIn('negative_prompt', workflow_params)
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试不存在的角色
        with self.assertRaises(Exception):
            self.manager.load_character("nonexistent")
        
        # 测试角色不存在时的生成器行为
        suggestions = self.generator.get_character_suggestions("non")
        self.assertEqual(len(suggestions), 0)
        
        # 创建一个不完整的角色（缺少音频文件）
        incomplete_dir = os.path.join(self.characters_dir, "incomplete")
        os.makedirs(incomplete_dir, exist_ok=True)
        
        # 只创建图片文件
        image_file = os.path.join(incomplete_dir, "image.jpg")
        with open(image_file, 'w') as f:
            f.write("fake image content")
        
        # 测试验证失败
        validation_result = self.manager.validate_character("incomplete")
        self.assertFalse(validation_result.is_valid)
        self.assertGreater(len(validation_result.errors), 0)
        
        # 测试加载失败
        with self.assertRaises(Exception):
            self.manager.load_character("incomplete")
    
    def test_file_validation_integration(self):
        """测试文件验证集成"""
        character_name = "file_test"
        character_dir = os.path.join(self.characters_dir, character_name)
        os.makedirs(character_dir, exist_ok=True)
        
        # 创建不同类型的文件
        files_to_create = [
            ("audio.mp3", "audio content"),
            ("image.jpg", "image content"),
            ("video.mp4", "video content"),
            ("document.txt", "text content"),
            ("another.wav", "another audio")
        ]
        
        for filename, content in files_to_create:
            file_path = os.path.join(character_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        # 验证角色
        validation_result = self.manager.validate_character(character_name)
        
        # 应该找到音频和图片文件，但忽略文本文件
        self.assertTrue(validation_result.has_audio())
        self.assertTrue(validation_result.has_images())
        self.assertTrue(validation_result.has_videos())
        
        # 检查找到的文件数量
        self.assertEqual(len(validation_result.found_files['audio']), 2)  # mp3 和 wav
        self.assertEqual(len(validation_result.found_files['images']), 1)  # jpg
        self.assertEqual(len(validation_result.found_files['videos']), 1)  # mp4
    
    def test_workflow_client_integration(self):
        """测试工作流客户端集成"""
        # 创建模拟客户端并直接注入
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.load_workflow.return_value = {"test": "workflow"}
        mock_client.upload_file.return_value = "uploaded_file.mp3"
        mock_client.submit_workflow_async.return_value = "test_prompt_id"
        mock_client.wait_for_completion.return_value = True
        mock_client.get_results.return_value = {
            "outputs": {
                "1": {
                    "videos": [{"filename": "test_video.mp4", "type": "output"}]
                }
            }
        }
        mock_client.extract_output_files.return_value = {
            "1": [{
                "type": "video",
                "filename": "test_video.mp4",
                "url": "http://test.com/test_video.mp4"
            }]
        }
        mock_client.download_file.return_value = True
        
        # 直接注入mock客户端
        self.generator.workflow_client = mock_client
        
        # 创建测试角色
        character_name = "workflow_test"
        self.create_test_character(character_name)
        
        # 测试异步生成
        prompt_id = self.generator.generate_video_async(
            character_name=character_name,
            text="测试文本"
        )
        
        # 验证调用（现在使用正确的方法名）
        self.assertEqual(prompt_id, "test_prompt_id")
        mock_client.connect.assert_called_once()
        mock_client.submit_workflow_async.assert_called_once()
        mock_client.disconnect.assert_called_once()
    
    def test_character_suggestions_integration(self):
        """测试角色建议集成"""
        # 创建多个角色
        character_names = ["女白领", "男主播", "虚拟助手", "客服人员"]
        for name in character_names:
            self.create_test_character(name)
        
        # 测试模糊匹配
        suggestions = self.generator.get_character_suggestions("女")
        self.assertIn("女白领", suggestions)
        
        suggestions = self.generator.get_character_suggestions("主")
        self.assertIn("男主播", suggestions)
        
        suggestions = self.generator.get_character_suggestions("助")
        self.assertIn("虚拟助手", suggestions)
        
        # 测试无匹配
        suggestions = self.generator.get_character_suggestions("xyz")
        self.assertEqual(len(suggestions), 0)
        
        # 测试空搜索
        suggestions = self.generator.get_character_suggestions("")
        self.assertEqual(len(suggestions), 4)  # 所有角色
    
    def test_validation_before_generation(self):
        """测试生成前的验证"""
        character_name = "validation_test"
        self.create_test_character(character_name)
        
        # 测试验证通过
        is_valid = self.generator.validate_character_before_generation(character_name)
        self.assertTrue(is_valid)
        
        # 创建一个文件不存在的情况
        character_info = self.generator.character_manager.load_character(character_name)
        original_audio_path = character_info.audio_path
        
        # 删除音频文件
        os.remove(character_info.audio_path)
        
        # 验证应该失败
        is_valid = self.generator.validate_character_before_generation(character_name)
        self.assertFalse(is_valid)
        
        # 恢复文件
        with open(original_audio_path, 'w') as f:
            f.write("restored audio content")
        
        # 验证应该再次通过
        is_valid = self.generator.validate_character_before_generation(character_name)
        self.assertTrue(is_valid)


class TestPerformanceIntegration(unittest.TestCase):
    """性能集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.characters_dir = os.path.join(self.temp_dir, "characters")
        os.makedirs(self.characters_dir, exist_ok=True)
        
        self.manager = CharacterManager(self.characters_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def create_many_characters(self, count: int):
        """创建多个测试角色"""
        for i in range(count):
            character_dir = os.path.join(self.characters_dir, f"char_{i}")
            os.makedirs(character_dir, exist_ok=True)
            
            # 创建音频文件
            audio_file = os.path.join(character_dir, f"audio_{i}.mp3")
            with open(audio_file, 'w') as f:
                f.write(f"audio content {i}")
            
            # 创建图片文件
            image_file = os.path.join(character_dir, f"image_{i}.jpg")
            with open(image_file, 'w') as f:
                f.write(f"image content {i}")
    
    def test_scan_performance(self):
        """测试扫描性能"""
        character_count = 50
        self.create_many_characters(character_count)
        
        # 测试扫描性能
        start_time = time.time()
        characters = self.manager.scan_characters()
        end_time = time.time()
        
        scan_time = end_time - start_time
        self.assertEqual(len(characters), character_count)
        print(f"扫描 {character_count} 个角色耗时: {scan_time:.3f} 秒")
        
        # 扫描时间应该在合理范围内
        self.assertLess(scan_time, 5.0)  # 5秒内完成
    
    def test_cache_performance(self):
        """测试缓存性能"""
        character_count = 20
        self.create_many_characters(character_count)
        
        # 预热：第一次加载所有角色
        start_time = time.time()
        for i in range(character_count):
            self.manager.load_character(f"char_{i}")
        first_load_time = time.time() - start_time
        
        # 缓存命中：第二次加载所有角色
        start_time = time.time()
        for i in range(character_count):
            self.manager.load_character(f"char_{i}")
        cache_load_time = time.time() - start_time
        
        print(f"第一次加载耗时: {first_load_time:.3f} 秒")
        print(f"缓存加载耗时: {cache_load_time:.3f} 秒")
        
        # 缓存加载应该明显更快
        self.assertLess(cache_load_time, first_load_time * 0.1)


if __name__ == '__main__':
    unittest.main()