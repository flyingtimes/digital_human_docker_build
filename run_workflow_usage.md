# 数字人生成工作流客户端使用说明

## 功能特点

- 🚀 支持运行完整的数字人生成工作流
- 📊 实时进度监控，支持详细节点状态显示
- 🔄 支持根据prompt_id重新获取生成结果
- 🎯 专门的任务进度监控模式
- ⚙️ 完整的命令行参数配置
- 📝 详细的进度和结果反馈

## 使用方法

### 1. 运行工作流生成数字人视频（推荐）

```bash
# 使用默认参数运行（包含实时进度显示）
python run_workflow.py

# 自定义参数运行
python run_workflow.py \
    --mode run \
    --server 127.0.0.1:6006 \
    --workflow voice-video-04-api.json \
    --audio awoman2.mp3 \
    --video kaka2.png \
    --text "这个的速度为什么变快了" \
    --positive "A woman passionately talking" \
    --output outputs \
    --timeout 600
```

### 2. 仅监控任务进度

```bash
# 监控指定prompt_id的任务进度（不下载结果）
python run_workflow.py \
    --mode monitor \
    --prompt_id "your-prompt-id-here" \
    --timeout 600
```

### 3. 获取指定prompt_id的结果

如果之前运行的生成功流被中断，或者想要重新下载结果：

```bash
# 使用prompt_id获取结果
python run_workflow.py \
    --mode get_result \
    --prompt_id "your-prompt-id-here" \
    --output outputs
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式：run(运行工作流) \| get_result(获取结果) \| monitor(仅监控进度) | run |
| `--server` | ComfyUI服务器地址 | 127.0.0.1:6006 |
| `--workflow` | 工作流配置文件路径 | voice-video-04-api.json |
| `--audio` | 音频文件路径 | awoman2.mp3 |
| `--video` | 视频参考图像路径 | kaka2.png |
| `--text` | 文本提示 | "这个的速度为什么变快了" |
| `--positive` | 正面提示词 | "A woman passionately talking" |
| `--output` | 输出目录 | outputs |
| `--prompt_id` | 指定要获取结果或监控的prompt_id | 无 |
| `--timeout` | 超时时间（秒） | 600 |

## 进度显示说明

程序提供三种进度显示方式：

1. **节点状态显示**：✅已完成 | 🔄执行中 | ⏳等待中 | ❌错误
2. **百分比进度**：📊 进度: 45.2% (9/20)
3. **总体进度**：📈 总进度: 60.0% | ✅12 | 🔄1 | ⏳7 (总计: 20)

## 输出说明

程序运行成功后会在指定的输出目录中生成以下文件：
- 视频文件（.mp4格式）
- 可能包含音频文件、图像文件等

## 工作流程建议

### 完整工作流程：
```bash
# 1. 提交任务（会返回prompt_id）
python run_workflow.py

# 2. 如果需要，可以单独监控进度
python run_workflow.py --mode monitor --prompt_id "your-prompt-id"

# 3. 下载结果
python run_workflow.py --mode get_result --prompt_id "your-prompt-id"
```

### 注意事项

1. 🖥️ 确保ComfyUI服务器正在运行并且可访问
2. 📁 确保指定的音频和视频文件存在
3. 💾 确保有足够的磁盘空间存储生成的文件
4. ⏱️ 生成过程可能需要较长时间，请耐心等待
5. 🔄 可以随时使用Ctrl+C中断程序，然后用prompt_id重新获取结果

## 示例输出

### 运行工作流模式：
```
=== 开始运行数字人生成工作流 ===
工作流配置: voice-video-04-api.json
音频文件: awoman2.mp3
图像文件: kaka2.png
文本提示: 这个的速度为什么变快了
输出目录: outputs
超时时间: 600秒
==================================================
已连接到服务器: 127.0.0.1:6006
工作流配置加载成功: voice-video-04-api.json
正在上传文件: awoman2.mp3
文件上传成功: awoman2.mp3 -> awoman2.mp3
正在上传文件: kaka2.png
文件上传成功: kaka2.png -> kaka2.png
工作流提交成功，Prompt ID: 0d7c242e-9af9-4c0c-866b-688579c1b0e2
📈 总进度: 25.0% | ✅5 | 🔄1 | ⏳15 (总计: 21)
📊 进度: 50.0% (10/20)
✅ 工作流执行完成
获取执行结果成功
生成文件数量: 1
文件已保存: outputs\generated_video.mp4

✅ 数字人生成完成！
🎯 Prompt ID: 0d7c242e-9af9-4c0c-866b-688579c1b0e2
💾 输出目录: outputs

💡 其他可用命令：
  • 重新获取结果: python run_workflow.py --mode get_result --prompt_id 0d7c242e-9af9-4c0c-866b-688579c1b0e2
  • 仅监控进度: python run_workflow.py --mode monitor --prompt_id 0d7c242e-9af9-4c0c-866b-688579c1b0e2
```

### 监控进度模式：
```
=== 监控数字人生成进度 ===
Prompt ID: 0d7c242e-9af9-4c0c-866b-688579c1b0e2
超时时间: 600秒
🔍 正在连接服务器并监控任务进度...
==================================================
📈 总进度: 15.0% | ✅3 | 🔄1 | ⏳17 (总计: 21)
📈 总进度: 30.0% | ✅6 | 🔄2 | ⏳13 (总计: 21)
📈 总进度: 65.0% | ✅14 | 🔄1 | ⏳6 (总计: 21)
📈 总进度: 90.0% | ✅19 | 🔄1 | ⏳1 (总计: 21)
✅ 任务完成！

✅ 监控完成！任务已成功执行。
💡 如需下载结果，请运行: python run_workflow.py --mode get_result --prompt_id 0d7c242e-9af9-4c0c-866b-688579c1b0e2
```
