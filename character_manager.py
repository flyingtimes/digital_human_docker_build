#!/usr/bin/env python3
"""
数字人角色管理器 - 命令行界面
"""

import argparse
import sys
import os
import logging
from typing import List, Optional
from pathlib import Path

from character_manager_core import CharacterManager
from digital_human_generator import DigitalHumanGenerator
from character_models import CharacterError, CharacterNotFoundError, CharacterValidationError


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


class CharacterManagerCLI:
    """数字人角色管理器命令行界面"""
    
    def __init__(self):
        self.character_manager = CharacterManager()
        self.generator = DigitalHumanGenerator()
    
    def cmd_list(self, args):
        """列出所有角色"""
        print("📋 可用的数字人角色:")
        print("=" * 50)
        
        try:
            characters = self.character_manager.list_characters()
            
            if not characters:
                print("📝 当前没有可用的角色")
                print(f"💡 请在 '{self.character_manager.characters_dir}' 目录下创建角色文件夹")
                print(f"   每个角色文件夹需要包含:")
                print(f"   - 参考音频文件 (.mp3, .wav, .m4a)")
                print(f"   - 参考图片文件 (.jpg, .png) 或 视频文件 (.mp4)")
                return
            
            for i, character_name in enumerate(characters, 1):
                try:
                    character_info = self.character_manager.get_character_info(character_name)
                    if character_info:
                        print(f"{i:2d}. {character_name}")
                        print(f"     🎵 音频: {Path(character_info.audio_path).name}")
                        print(f"     🖼️  视觉: {Path(character_info.visual_path).name} ({character_info.visual_type})")
                        
                        # 显示描述
                        if character_info.config.get('description'):
                            print(f"     📝 描述: {character_info.config['description']}")
                        
                        print()
                except Exception as e:
                    print(f"{i:2d}. {character_name} (加载失败: {e})")
                    print()
            
            print(f"📊 总共 {len(characters)} 个角色")
            
        except Exception as e:
            print(f"❌ 列出角色失败: {e}")
    
    def cmd_info(self, args):
        """显示角色详细信息"""
        character_name = args.character_name
        
        try:
            summary = self.character_manager.get_character_summary(character_name)
            if summary:
                print(f"🎭 角色详细信息: {character_name}")
                print("=" * 50)
                print(summary)
            else:
                print(f"❌ 角色不存在: {character_name}")
                self._suggest_characters()
        
        except Exception as e:
            print(f"❌ 获取角色信息失败: {e}")
    
    def cmd_validate(self, args):
        """验证角色"""
        character_name = args.character_name
        
        try:
            print(f"🔍 验证角色: {character_name}")
            print("=" * 50)
            
            result = self.character_manager.validate_character(character_name)
            
            if result.is_valid:
                print("✅ 角色验证通过")
            else:
                print("❌ 角色验证失败")
                print("错误:")
                for error in result.errors:
                    print(f"  - {error}")
            
            if result.warnings:
                print("⚠️  警告:")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            # 显示找到的文件
            print("📁 找到的文件:")
            for file_type, files in result.found_files.items():
                if files:
                    print(f"  {file_type}: {len(files)} 个")
                    for file in files:
                        print(f"    - {Path(file).name}")
            
        except Exception as e:
            print(f"❌ 验证失败: {e}")
    
    def cmd_generate(self, args):
        """生成数字人视频"""
        character_name = args.character_name
        text = args.text
        
        # 检查是否为交互模式
        if text == "-":
            try:
                print("📝 请输入要生成的文本内容 (Ctrl+D 或输入 'quit' 结束):")
                lines = []
                while True:
                    try:
                        line = input("> ")
                        if line.strip() == 'quit':
                            break
                        lines.append(line)
                    except EOFError:
                        break
                
                text = "\n".join(lines)
                if not text.strip():
                    print("❌ 没有输入文本内容")
                    return
                
                print(f"\n📝 将生成以下内容:")
                print("-" * 30)
                print(text)
                print("-" * 30)
                
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                return
        
        # 生成视频
        prompt_id = self.generator.generate_video(
            character_name=character_name,
            text=text,
            positive_prompt=args.positive,
            negative_prompt=args.negative,
            workflow_path=args.workflow,
            timeout=args.timeout
        )
        
        if prompt_id:
            print(f"\n💡 其他可用命令:")
            print(f"  • 监控进度: python character_manager.py monitor {prompt_id}")
            print(f"  • 获取结果: python character_manager.py result {prompt_id}")
            print(f"  • 重新生成: python character_manager.py generate {character_name} \"{text}\"")
    
    def cmd_generate_async(self, args):
        """异步生成数字人视频"""
        character_name = args.character_name
        text = args.text
        
        prompt_id = self.generator.generate_video_async(
            character_name=character_name,
            text=text,
            positive_prompt=args.positive,
            negative_prompt=args.negative,
            workflow_path=args.workflow
        )
        
        if prompt_id:
            print(f"\n💡 其他可用命令:")
            print(f"  • 监控进度: python character_manager.py monitor {prompt_id}")
            print(f"  • 获取结果: python character_manager.py result {prompt_id}")
    
    def cmd_monitor(self, args):
        """监控任务进度"""
        prompt_id = args.prompt_id
        
        success = self.generator.monitor_progress_only(
            prompt_id=prompt_id,
            timeout=args.timeout,
            auto_download=not args.no_download
        )
        
        if success:
            print(f"✅ 监控完成")
        else:
            print(f"❌ 监控失败")
            sys.exit(1)
    
    def cmd_result(self, args):
        """获取任务结果"""
        prompt_id = args.prompt_id
        
        success = self.generator.get_result_by_prompt_id(prompt_id=prompt_id)
        
        if success:
            print(f"✅ 结果获取完成")
        else:
            print(f"❌ 结果获取失败")
            sys.exit(1)
    
    def cmd_init(self, args):
        """初始化角色目录"""
        characters_dir = args.characters_dir or self.character_manager.characters_dir
        
        try:
            if not os.path.exists(characters_dir):
                os.makedirs(characters_dir)
                print(f"✅ 创建角色目录: {characters_dir}")
            else:
                print(f"✅ 角色目录已存在: {characters_dir}")
            
            # 创建示例角色
            if args.create_example:
                self._create_example_character(characters_dir, args.example_name)
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
    
    def cmd_cache(self, args):
        """缓存管理"""
        if args.clear:
            self.character_manager.clear_cache()
            print("✅ 缓存已清除")
        else:
            stats = self.character_manager.get_cache_stats()
            print("📊 缓存统计:")
            print(f"  总条目: {stats['total_entries']}")
            print(f"  有效条目: {stats['active_entries']}")
            print(f"  过期条目: {stats['expired_entries']}")
    
    def _create_example_character(self, characters_dir: str, character_name: str):
        """创建示例角色"""
        try:
            from character_models import CharacterConfig
            
            character_dir = os.path.join(characters_dir, character_name)
            os.makedirs(character_dir, exist_ok=True)
            
            # 创建配置文件
            config = CharacterConfig.create_default_config()
            config['description'] = f"示例角色 - {character_name}"
            config['tags'] = ['示例']
            
            CharacterConfig.save_config(character_dir, config)
            
            # 创建说明文件
            readme_path = os.path.join(character_dir, "README.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"""角色: {character_name}
===================

这是 {character_name} 角色的文件夹。

需要添加的文件:
1. 参考音频文件 (支持的格式: .mp3, .wav, .m4a)
2. 参考图片文件 (支持的格式: .jpg, .png, .webp) 或 参考视频文件 (支持的格式: .mp4, .avi, .mov)

可选文件:
- config.json: 角色配置文件
- README.txt: 角色说明文件

配置说明:
- positive_prompt: 正面提示词
- negative_prompt: 负面提示词
- workflow_params: 工作流参数
- description: 角色描述
- tags: 角色标签

示例用法:
python character_manager.py generate {character_name} "要生成的文本内容"
""")
            
            print(f"✅ 创建示例角色: {character_name}")
            print(f"   📁 角色目录: {character_dir}")
            print(f"   ⚙️  配置文件: {os.path.join(character_dir, 'config.json')}")
            print(f"   📖 说明文件: {readme_path}")
            
        except Exception as e:
            print(f"❌ 创建示例角色失败: {e}")
    
    def _suggest_characters(self):
        """建议角色"""
        try:
            characters = self.character_manager.list_characters()
            if characters:
                print("💡 可用的角色:")
                for char in characters:
                    print(f"   - {char}")
            else:
                print("💡 当前没有可用的角色")
                print("   使用 'character_manager.py init --create-example' 创建示例角色")
        except Exception as e:
            print(f"❌ 无法获取角色列表: {e}")
    
    def run(self):
        """运行命令行界面"""
        parser = argparse.ArgumentParser(
            description="数字人角色管理器",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  # 初始化角色目录
  python character_manager.py init --create-example --example-name "女白领"
  
  # 列出所有角色
  python character_manager.py list
  
  # 查看角色信息
  python character_manager.py info "女白领"
  
  # 验证角色
  python character_manager.py validate "女白领"
  
  # 生成数字人视频
  python character_manager.py generate "女白领" "这是一个测试视频"
  
  # 异步生成
  python character_manager.py generate-async "女白领" "这是一个测试视频"
  
  # 监控任务进度
  python character_manager.py monitor <prompt_id>
  
  # 获取任务结果
  python character_manager.py result <prompt_id>
            """
        )
        
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='详细输出')
        parser.add_argument('--characters-dir', default='characters',
                           help='角色目录路径')
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # list 命令
        subparsers.add_parser('list', help='列出所有角色')
        
        # info 命令
        info_parser = subparsers.add_parser('info', help='显示角色详细信息')
        info_parser.add_argument('character_name', help='角色名称')
        
        # validate 命令
        validate_parser = subparsers.add_parser('validate', help='验证角色')
        validate_parser.add_argument('character_name', help='角色名称')
        
        # generate 命令
        generate_parser = subparsers.add_parser('generate', help='生成数字人视频')
        generate_parser.add_argument('character_name', help='角色名称')
        generate_parser.add_argument('text', help='要生成的文本内容 (使用 "-" 进入交互模式)')
        generate_parser.add_argument('--positive', help='正面提示词')
        generate_parser.add_argument('--negative', help='负面提示词')
        generate_parser.add_argument('--workflow', help='工作流配置文件路径')
        generate_parser.add_argument('--timeout', type=int, default=600, help='超时时间（秒）')
        
        # generate-async 命令
        async_parser = subparsers.add_parser('generate-async', help='异步生成数字人视频')
        async_parser.add_argument('character_name', help='角色名称')
        async_parser.add_argument('text', help='要生成的文本内容')
        async_parser.add_argument('--positive', help='正面提示词')
        async_parser.add_argument('--negative', help='负面提示词')
        async_parser.add_argument('--workflow', help='工作流配置文件路径')
        
        # monitor 命令
        monitor_parser = subparsers.add_parser('monitor', help='监控任务进度')
        monitor_parser.add_argument('prompt_id', help='任务ID')
        monitor_parser.add_argument('--timeout', type=int, default=600, help='超时时间（秒）')
        monitor_parser.add_argument('--no-download', action='store_true', help='不自动下载结果')
        
        # result 命令
        result_parser = subparsers.add_parser('result', help='获取任务结果')
        result_parser.add_argument('prompt_id', help='任务ID')
        
        # init 命令
        init_parser = subparsers.add_parser('init', help='初始化角色目录')
        init_parser.add_argument('--characters-dir', help='角色目录路径')
        init_parser.add_argument('--create-example', action='store_true', help='创建示例角色')
        init_parser.add_argument('--example-name', default='示例角色', help='示例角色名称')
        
        # cache 命令
        cache_parser = subparsers.add_parser('cache', help='缓存管理')
        cache_parser.add_argument('--clear', action='store_true', help='清除缓存')
        
        args = parser.parse_args()
        
        # 设置日志
        setup_logging(args.verbose)
        
        # 更新角色目录
        if args.characters_dir:
            self.character_manager.characters_dir = args.characters_dir
            self.generator.character_manager.characters_dir = args.characters_dir
        
        # 执行命令
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == 'list':
                self.cmd_list(args)
            elif args.command == 'info':
                self.cmd_info(args)
            elif args.command == 'validate':
                self.cmd_validate(args)
            elif args.command == 'generate':
                self.cmd_generate(args)
            elif args.command == 'generate-async':
                self.cmd_generate_async(args)
            elif args.command == 'monitor':
                self.cmd_monitor(args)
            elif args.command == 'result':
                self.cmd_result(args)
            elif args.command == 'init':
                self.cmd_init(args)
            elif args.command == 'cache':
                self.cmd_cache(args)
            else:
                parser.print_help()
        
        except KeyboardInterrupt:
            print("\n❌ 用户取消")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    cli = CharacterManagerCLI()
    cli.run()


if __name__ == "__main__":
    main()