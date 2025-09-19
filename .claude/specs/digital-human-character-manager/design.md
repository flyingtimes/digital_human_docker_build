# Design Document

## 概述

本文档描述了数字人角色管理功能的系统设计。该功能旨在通过标准化的文件夹结构简化数字人创建流程，让用户只需输入角色名称和文本内容即可生成数字人播报视频。

## 架构设计

### 系统架构

```
数字人角色管理系统
├── 角色管理模块 (CharacterManager)
│   ├── 角色扫描器 (CharacterScanner)
│   ├── 角色验证器 (CharacterValidator)
│   └── 角色加载器 (CharacterLoader)
├── 工作流适配器 (WorkflowAdapter)
│   ├── 参数生成器 (ParameterGenerator)
│   └── 结果处理器 (ResultHandler)
└── 用户界面模块 (CLI Interface)
    ├── 命令解析器 (CommandParser)
    └── 输出格式化器 (OutputFormatter)
```

### 核心组件

#### 1. CharacterManager（角色管理器）
- **职责**: 管理数字人角色的扫描、验证和加载
- **接口**: `scan_characters()`, `validate_character()`, `load_character()`
- **数据结构**: 角色信息字典，包含音频、图像/视频路径

#### 2. WorkflowAdapter（工作流适配器）
- **职责**: 适配现有的run_workflow.py，提供简化的接口
- **接口**: `generate_video(character_name, text)`
- **设计模式**: 适配器模式

## 详细设计

### 1. 文件夹结构设计

```
项目根目录/
├── characters/                  # 角色根目录
│   ├── 女白领/                  # 角色文件夹
│   │   ├── reference_audio.mp3  # 参考音频
│   │   ├── reference_image.jpg  # 参考图片
│   │   └── config.json         # 可选配置
│   ├── 男主播/
│   │   ├── reference_audio.wav
│   │   └── reference_video.mp4
│   └── 虚拟助手/
│       ├── reference_audio.mp3
│       └── reference_image.png
├── run_workflow.py             # 现有工作流
├── character_manager.py        # 新增角色管理器
└── outputs/                    # 输出目录
```

### 2. 角色信息模型

```python
class CharacterInfo:
    def __init__(self, name: str, audio_path: str, visual_path: str, visual_type: str):
        self.name = name                    # 角色名称
        self.audio_path = audio_path        # 音频文件路径
        self.visual_path = visual_path      # 图像/视频路径
        self.visual_type = visual_type      # 'image' 或 'video'
        self.config = {}                   # 可选配置
        self.validation_result = None       # 验证结果
```

### 3. CharacterManager 类设计

```python
class CharacterManager:
    def __init__(self, characters_dir: str = "characters"):
        self.characters_dir = characters_dir
        self.characters = {}    # 缓存角色信息
        self.supported_audio_formats = ['.mp3', '.wav', '.m4a']
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.webp']
        self.supported_video_formats = ['.mp4', '.avi', '.mov']
    
    def scan_characters(self) -> Dict[str, CharacterInfo]:
        """扫描characters目录，返回所有有效角色"""
        pass
    
    def validate_character(self, character_name: str) -> ValidationResult:
        """验证角色文件夹的完整性"""
        pass
    
    def load_character(self, character_name: str) -> Optional[CharacterInfo]:
        """加载指定角色的信息"""
        pass
    
    def list_characters(self) -> List[str]:
        """列出所有可用角色名称"""
        pass
```

### 4. 工作流适配器设计

```python
class DigitalHumanGenerator:
    def __init__(self, server_address: str = "127.0.0.1:6006"):
        self.character_manager = CharacterManager()
        self.workflow_client = DigitalHumanWorkflowClient(server_address)
        self.default_workflow = "voice-video-04-api.json"
        self.output_dir = "outputs"
    
    def generate_video(self, character_name: str, text: str, 
                      positive_prompt: str = None, negative_prompt: str = None) -> str:
        """生成数字人视频的主要接口"""
        pass
    
    def setup_character_workflow(self, character: CharacterInfo, text: str,
                               positive_prompt: str, negative_prompt: str) -> Dict:
        """为特定角色设置工作流参数"""
        pass
```

## 接口设计

### 1. 命令行接口

```bash
# 新的简化命令
python character_manager.py generate <角色名称> <文本内容> [--positive <提示词>] [--negative <提示词>]

# 管理命令
python character_manager.py list                    # 列出所有角色
python character_manager.py validate <角色名称>     # 验证角色
python character_manager.py info <角色名称>         # 显示角色信息
```

### 2. 配置文件接口

每个角色文件夹可包含可选的 `config.json`：

```json
{
  "positive_prompt": "A woman passionately talking",
  "negative_prompt": "bright tones, overexposed, static",
  "workflow_params": {
    "temperature": 0.8,
    "top_k": 30
  }
}
```

## 错误处理设计

### 1. 错误类型定义

```python
class CharacterError(Exception):
    """角色相关错误基类"""
    pass

class CharacterNotFoundError(CharacterError):
    """角色不存在错误"""
    pass

class CharacterValidationError(CharacterError):
    """角色验证失败错误"""
    pass

class FileNotFoundError(CharacterError):
    """必需文件不存在错误"""
    pass
```

### 2. 验证流程

```python
def validate_character(self, character_name: str) -> ValidationResult:
    """验证角色文件夹"""
    result = ValidationResult(character_name)
    
    # 检查文件夹是否存在
    character_dir = os.path.join(self.characters_dir, character_name)
    if not os.path.exists(character_dir):
        result.add_error("角色文件夹不存在")
        return result
    
    # 检查音频文件
    audio_files = self._find_audio_files(character_dir)
    if not audio_files:
        result.add_error("缺少参考音频文件")
    
    # 检查图像/视频文件
    visual_files = self._find_visual_files(character_dir)
    if not visual_files:
        result.add_error("缺少参考图像或视频文件")
    
    return result
```

## 数据模型

### 1. ValidationResult 模型

```python
class ValidationResult:
    def __init__(self, character_name: str):
        self.character_name = character_name
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.found_files = {
            'audio': [],
            'images': [],
            'videos': []
        }
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
```

## 性能考虑

### 1. 缓存策略
- 角色信息缓存：避免重复扫描文件系统
- 配置文件缓存：避免重复读取JSON文件
- 失败缓存：避免重复验证失败的角色

### 2. 文件扫描优化
- 使用 `os.scandir()` 替代 `os.listdir()` 提升性能
- 支持的文件格式检查使用集合查找，时间复杂度O(1)
- 异步文件验证（对于大量文件时）

## 安全考虑

### 1. 路径验证
- 防止路径遍历攻击（如 `../../../etc/passwd`）
- 规范化路径处理
- 文件类型白名单验证

### 2. 输入验证
- 角色名称验证（不允许特殊字符）
- 文件大小限制
- 文件格式验证

## 测试策略

### 1. 单元测试
- `CharacterManager` 的各个方法
- 文件扫描和验证逻辑
- 错误处理机制

### 2. 集成测试
- 与现有 `run_workflow.py` 的集成
- 端到端的视频生成流程

### 3. 测试数据
```python
# 测试角色结构
test_characters = {
    'valid_character': {
        'audio': 'test_audio.mp3',
        'image': 'test_image.jpg'
    },
    'missing_audio': {
        'image': 'test_image.jpg'
    },
    'missing_visual': {
        'audio': 'test_audio.mp3'
    }
}
```

## 扩展性设计

### 1. 插件化架构
- 支持自定义验证器
- 支持自定义文件处理器
- 支持多种工作流后端

### 2. 配置系统
- 全局配置文件
- 角色级配置覆盖
- 环境变量支持

## 向后兼容性

### 1. 现有接口保持
- 原有的 `run_workflow.py` 功能保持不变
- 新功能作为附加模块提供

### 2. 迁移路径
- 渐进式迁移策略
- 并行运行期支持