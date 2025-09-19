# 数字人角色管理系统

这是一个用于管理数字人角色并简化数字人视频生成流程的系统。

## 功能特点

- 🎭 **角色管理**: 轻松管理多个数字人角色
- 📁 **标准化结构**: 统一的角色文件夹结构
- 🎯 **简化操作**: 一键生成数字人视频
- ⚙️ **配置灵活**: 支持角色级别的自定义配置
- 🔄 **缓存优化**: 智能缓存提升性能
- 🔍 **验证机制**: 自动验证角色完整性

## 快速开始

### 1. 初始化系统

```bash
# 初始化角色目录
python character_manager.py init

# 创建示例角色
python character_manager.py init --create-example --example-name "女白领"
```

### 2. 查看可用角色

```bash
# 列出所有角色
python character_manager.py list

# 查看角色详细信息
python character_manager.py info "女白领"

# 验证角色
python character_manager.py validate "女白领"
```

### 3. 生成数字人视频

```bash
# 基本用法
python character_manager.py generate "女白领" "这是一个测试视频"

# 自定义提示词
python character_manager.py generate "女白领" "测试文本" --positive "A professional woman talking"

# 交互模式输入文本
python character_manager.py generate "女白领" -

# 异步生成
python character_manager.py generate-async "女白领" "测试文本"
```

### 4. 监控和获取结果

```bash
# 监控任务进度
python character_manager.py monitor <prompt_id>

# 获取任务结果
python character_manager.py result <prompt_id>

# 清除缓存
python character_manager.py cache --clear
```

## 角色文件夹结构

每个角色需要按照以下结构组织：

```
characters/
├── 女白领/
│   ├── 参考音频.mp3          # 必需：音频参考文件
│   ├── 参考图片.png          # 必需：图片或视频参考文件
│   ├── config.json           # 可选：角色配置
│   └── README.txt            # 可选：角色说明
└── 男主播/
    ├── 参考音频.mp3
    ├── 参考图片.png
    └── config.json
```

### 支持的文件格式

- **音频**: .mp3, .wav, .m4a, .flac, .aac, .ogg
- **图片**: .jpg, .jpeg, .png, .webp, .bmp, .tiff, .gif
- **视频**: .mp4, .avi, .mov, .mkv, .flv, .webm

## 配置文件

每个角色可以有一个 `config.json` 配置文件：

```json
{
  "positive_prompt": "A professional woman passionately talking in office setting",
  "negative_prompt": "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background",
  "workflow_params": {
    "temperature": 0.8,
    "top_k": 30,
    "top_p": 0.8,
    "num_beams": 3
  },
  "description": "专业女白领角色，适合商务、办公场景的数字人播报",
  "tags": ["女白领", "商务", "办公", "专业"]
}
```

## 命令行选项

### 全局选项

- `--verbose, -v`: 详细输出
- `--characters-dir`: 指定角色目录路径

### 子命令

#### `init` - 初始化
- `--create-example`: 创建示例角色
- `--example-name`: 示例角色名称
- `--characters-dir`: 角色目录路径

#### `list` - 列出角色
- 无参数

#### `info` - 角色信息
- `character_name`: 角色名称

#### `validate` - 验证角色
- `character_name`: 角色名称

#### `generate` - 生成视频
- `character_name`: 角色名称
- `text`: 文本内容（使用 `-` 进入交互模式）
- `--positive`: 正面提示词
- `--negative`: 负面提示词
- `--workflow`: 工作流配置文件路径
- `--timeout`: 超时时间（秒）

#### `generate-async` - 异步生成
- `character_name`: 角色名称
- `text`: 文本内容
- `--positive`: 正面提示词
- `--negative`: 负面提示词
- `--workflow`: 工作流配置文件路径

#### `monitor` - 监控进度
- `prompt_id`: 任务ID
- `--timeout`: 超时时间（秒）
- `--no-download`: 不自动下载结果

#### `result` - 获取结果
- `prompt_id`: 任务ID

#### `cache` - 缓存管理
- `--clear`: 清除缓存

## 错误处理

系统提供详细的错误信息和解决建议：

- **角色不存在**: 提示创建角色的方法
- **验证失败**: 显示具体的错误信息
- **服务器连接问题**: 提供连接检查建议
- **文件缺失**: 提供文件检查步骤

## 性能优化

- **缓存机制**: 自动缓存角色信息，提升加载速度
- **文件扫描优化**: 使用高效的文件扫描算法
- **智能验证**: 预验证避免不必要的操作

## 故障排除

### 常见问题

1. **角色无法加载**
   - 检查角色文件夹结构是否正确
   - 确保必需的文件存在
   - 验证文件格式支持

2. **服务器连接失败**
   - 确保ComfyUI服务器正在运行
   - 检查服务器地址和端口
   - 验证网络连接

3. **生成任务失败**
   - 检查工作流配置文件
   - 验证服务器状态
   - 查看详细日志

### 调试命令

```bash
# 启用详细日志
python character_manager.py --verbose list

# 验证特定角色
python character_manager.py validate "角色名称"

# 清除缓存
python character_manager.py cache --clear
```

## 扩展功能

### 添加新角色

1. 在 `characters` 目录下创建角色文件夹
2. 添加参考音频和图片/视频文件
3. 可选：创建 `config.json` 配置文件
4. 使用 `validate` 命令验证角色完整性

### 自定义配置

- 修改角色的 `config.json` 文件
- 调整工作流参数
- 自定义提示词

## API 接口

### 编程接口

```python
from character_manager_core import CharacterManager
from digital_human_generator import DigitalHumanGenerator

# 创建角色管理器
manager = CharacterManager("characters")

# 创建生成器
generator = DigitalHumanGenerator()

# 生成视频
prompt_id = generator.generate_video(
    character_name="女白领",
    text="测试文本"
)
```

## 许可证

本项目遵循 MIT 许可证。

## 贡献

欢迎提交问题和改进建议！