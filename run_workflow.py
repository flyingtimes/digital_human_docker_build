#!/usr/bin/env python3
"""
数字人生成工作流调用程序
基于 voice-video-04-api.json 工作流配置
"""

import json
import websocket
import urllib.request
import urllib.parse
import uuid
import os
import time
import argparse
from typing import Dict, Any, Optional, Tuple


class DigitalHumanWorkflowClient:
    def __init__(self, server_address="127.0.0.1:6006"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def connect(self):
        """建立WebSocket连接"""
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            print(f"已连接到服务器: {self.server_address}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            self.ws.close()
            self.ws = None

    def upload_file(self, file_path: str, file_type: str = "input") -> Optional[str]:
        """
        上传文件到ComfyUI服务器

        Args:
            file_path: 本地文件路径
            file_type: 文件类型 (input, temp)

        Returns:
            上传后的文件名，失败返回None
        """
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None

        try:
            import requests

            print(f"正在上传文件: {file_path}")
            print(f"文件大小: {os.path.getsize(file_path)} bytes")
            print(f"服务器地址: {self.server_address}")

            with open(file_path, 'rb') as f:
                files = {'image': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {
                    'type': file_type,
                    'subfolder': ''
                }

                upload_url = f"http://{self.server_address}/upload/image"
                print(f"上传URL: {upload_url}")

                response = requests.post(
                    upload_url,
                    files=files,
                    data=data,
                    timeout=30
                )

                print(f"HTTP状态码: {response.status_code}")
                print(f"响应内容: {response.text}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"JSON响应: {result}")

                        # ComfyUI上传成功时会返回文件名、subfolder和type字段
                        if 'name' in result:
                            uploaded_name = result.get('name', os.path.basename(file_path))
                            print(f"文件上传成功: {file_path} -> {uploaded_name}")
                            return uploaded_name
                        else:
                            error_msg = result.get('error', '未知错误')
                            print(f"文件上传失败: {error_msg}")
                            return None
                    except ValueError as e:
                        print(f"解析JSON响应失败: {e}")
                        print(f"原始响应: {response.text}")
                        return None
                else:
                    print(f"HTTP请求失败: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    return None

        except ImportError:
            print("需要安装requests库: pip install requests")
            return None
        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"文件上传异常: {e}")
            return None

    def load_workflow(self, workflow_path: str) -> Optional[Dict[str, Any]]:
        """加载工作流配置文件"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            print(f"工作流配置加载成功: {workflow_path}")
            return workflow
        except Exception as e:
            print(f"工作流配置加载失败: {e}")
            return None

    def update_workflow_parameters(self, workflow: Dict[str, Any],
                                 audio_path: str, video_path: str,
                                 text_prompt: str, positive_prompt: str,
                                 negative_prompt: str = "") -> Dict[str, Any]:
        """
        更新工作流参数

        Args:
            workflow: 原始工作流配置
            audio_path: 音频文件路径
            video_path: 视频参考图像路径
            text_prompt: 文本提示
            positive_prompt: 正面提示词
            negative_prompt: 负面提示词
        """
        updated_workflow = workflow.copy()

        # 更新音频文件路径 (节点1)
        if audio_path:
            updated_workflow["1"]["inputs"]["audio"] = audio_path
            updated_workflow["1"]["inputs"]["audioUI"] = ""

        # 确保节点2有正确的音频输入连接（从节点1获取音频参考）
        if "2" in updated_workflow and "inputs" in updated_workflow["2"]:
            # 节点2是TTS节点，如果需要音频输入，应该连接到节点1
            if "audio" not in updated_workflow["2"]["inputs"]:
                updated_workflow["2"]["inputs"]["audio"] = ["1", 0]

        # 更新视频参考图像路径 (节点5)
        if video_path:
            updated_workflow["5"]["inputs"]["video"] = video_path

        # 更新文本提示 (节点3)
        if text_prompt:
            updated_workflow["3"]["inputs"]["multi_line_prompt"] = text_prompt

        # 更新正面提示词 (节点21)
        if positive_prompt:
            updated_workflow["21"]["inputs"]["positive_prompt"] = positive_prompt

        # 更新负面提示词 (节点21)
        if negative_prompt:
            updated_workflow["21"]["inputs"]["negative_prompt"] = negative_prompt

        # 更新音频保存节点 (节点4)
        updated_workflow["4"]["inputs"]["audioUI"] = ""

        return updated_workflow

    def submit_workflow(self, workflow: Dict[str, Any]) -> Optional[str]:
        """提交工作流到服务器"""
        try:
            prompt_id = str(uuid.uuid4())

            # 准备提交数据
            payload = {
                "prompt": workflow,
                "client_id": self.client_id,
                "prompt_id": prompt_id
            }

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
            req.add_header('Content-Type', 'application/json')

            # 发送请求
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                # 检查是否有node_errors，没有错误且有prompt_id就表示成功
                if 'prompt_id' in result and not result.get('node_errors', {}):
                    actual_prompt_id = result['prompt_id']
                    print(f"工作流提交成功，Prompt ID: {actual_prompt_id}")
                    return actual_prompt_id
                else:
                    print(f"工作流提交失败: {result}")
                    return None

        except Exception as e:
            print(f"工作流提交异常: {e}")
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 600, show_progress: bool = True) -> bool:
        """
        等待工作流执行完成

        Args:
            prompt_id: 工作流ID
            timeout: 超时时间（秒）
            show_progress: 是否显示详细进度信息

        Returns:
            是否成功完成
        """
        if not self.ws:
            print("WebSocket未连接")
            return False

        start_time = time.time()
        node_status = {}  # 跟踪节点状态
        last_progress_time = time.time()

        try:
            while time.time() - start_time < timeout:
                # 设置超时以避免阻塞
                self.ws.settimeout(1)
                try:
                    message = self.ws.recv()
                    if isinstance(message, str):
                        data = json.loads(message)

                        if data.get('type') == 'executing':
                            exec_data = data.get('data', {})
                            current_node = exec_data.get('node')
                            current_prompt_id = exec_data.get('prompt_id')

                            if current_prompt_id == prompt_id:
                                if current_node is None:
                                    print("\n✅ 工作流执行完成")
                                    return True
                                else:
                                    if show_progress:
                                        # 更新节点状态
                                        node_status[current_node] = 'executing'
                                        progress_text = self.format_progress_display(node_status)
                                        print(f"\r🔄 执行中: {progress_text}", end='', flush=True)

                        elif data.get('type') == 'progress':
                            progress = data.get('data', {})
                            value = progress.get('value', 0)
                            max_value = progress.get('max', 1)
                            if max_value > 0:
                                percentage = (value / max_value) * 100
                                if show_progress and time.time() - last_progress_time > 0.5:  # 限制更新频率
                                    print(f"\r📊 进度: {percentage:.1f}% ({value}/{max_value})", end='', flush=True)
                                    last_progress_time = time.time()

                        elif data.get('type') == 'progress_state':
                            # 详细的进度状态信息
                            progress_data = data.get('data', {})
                            if progress_data.get('prompt_id') == prompt_id:
                                nodes = progress_data.get('nodes', {})
                                if show_progress:
                                    # 更新所有节点状态
                                    for node_id, node_info in nodes.items():
                                        status = node_info.get('status', 'pending')
                                        node_status[node_id] = status

                                    # 计算总体进度
                                    overall_progress = self.calculate_overall_progress(nodes)
                                    progress_text = self.format_progress_display(node_status)
                                    print(f"\r📈 总进度: {overall_progress:.1%} | {progress_text}", end='', flush=True)

                        elif data.get('type') == 'error':
                            error_data = data.get('data', {})
                            print(f"\n❌ 执行错误: {error_data.get('exception_message', '未知错误')}")
                            return False

                except websocket.WebSocketTimeoutException:
                    # 每30秒检查一次任务是否还存在
                    if int(time.time() - start_time) % 30 == 0:
                        task_status = self.check_task_status(prompt_id)
                        if task_status == 'completed':
                            print("\n✅ 任务已在后台完成")
                            return True
                        elif task_status == 'not_found':
                            print("\n❌ 任务已不存在，可能已被清理")
                            return False
                    continue
                except Exception as e:
                    print(f"\n⚠️ 接收消息异常: {e}")
                    # 检查是否是连接问题，如果是，尝试重新连接
                    if "connection" in str(e).lower() or "socket" in str(e).lower():
                        print("🔄 尝试重新连接...")
                        self.disconnect()
                        if self.connect():
                            continue
                    break

            print(f"\n⏰ 等待超时 ({timeout}秒)")
            return False

        except Exception as e:
            print(f"\n❌ 等待执行异常: {e}")
            return False

    def calculate_overall_progress(self, nodes: Dict[str, Any]) -> float:
        """
        计算总体进度百分比

        Args:
            nodes: 节点状态信息

        Returns:
            进度百分比 (0.0-1.0)
        """
        if not nodes:
            return 0.0

        total_nodes = len(nodes)
        completed_nodes = 0

        for node_id, node_info in nodes.items():
            status = node_info.get('status', 'pending')
            if status in ['completed', 'success']:
                completed_nodes += 1

        return completed_nodes / total_nodes if total_nodes > 0 else 0.0

    def format_progress_display(self, node_status: Dict[str, str]) -> str:
        """
        格式化进度显示文本

        Args:
            node_status: 节点状态字典

        Returns:
            格式化的进度文本
        """
        if not node_status:
            return "准备中..."

        status_counts = {'pending': 0, 'executing': 0, 'completed': 0, 'error': 0}

        for status in node_status.values():
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts['pending'] += 1

        parts = []
        if status_counts['completed'] > 0:
            parts.append(f"✅{status_counts['completed']}")
        if status_counts['executing'] > 0:
            parts.append(f"🔄{status_counts['executing']}")
        if status_counts['pending'] > 0:
            parts.append(f"⏳{status_counts['pending']}")
        if status_counts['error'] > 0:
            parts.append(f"❌{status_counts['error']}")

        total = sum(status_counts.values())
        return f"{' | '.join(parts)} (总计: {total})"

    def check_task_status(self, prompt_id: str) -> Optional[str]:
        """
        检查任务状态
        
        Returns:
            'completed' - 任务已完成
            'running' - 任务正在运行
            'not_found' - 任务不存在
        """
        try:
            # 检查历史记录
            url = f"http://{self.server_address}/history/{prompt_id}"
            with urllib.request.urlopen(url) as response:
                history = json.loads(response.read().decode('utf-8'))
                if prompt_id in history:
                    return 'completed'
            
            # 检查队列
            queue_url = f"http://{self.server_address}/queue"
            with urllib.request.urlopen(queue_url) as response:
                queue_data = json.loads(response.read().decode('utf-8'))
                
                # 检查正在执行的任务
                # 队列项结构：[sequence_number, prompt_id, workflow, extra_data]
                for item in queue_data.get('queue_running', []):
                    if len(item) > 1 and item[1] == prompt_id:
                        return 'running'
                
                # 检查等待队列
                for item in queue_data.get('queue_pending', []):
                    if len(item) > 1 and item[1] == prompt_id:
                        return 'running'
            
            return 'not_found'
        except Exception as e:
            print(f"检查任务状态失败: {e}")
            return None

    def poll_for_completion(self, prompt_id: str, timeout: int = 600) -> bool:
        """
        使用轮询方式监控任务完成（避免WebSocket超时问题）
        
        Args:
            prompt_id: 工作流ID
            timeout: 超时时间（秒）
            
        Returns:
            是否成功完成
        """
        start_time = time.time()
        last_check_time = 0
        check_interval = 5  # 每5秒检查一次
        
        print("=" * 60)
        
        while time.time() - start_time < timeout:
            current_time = time.time()
            
            # 每隔一段时间检查一次状态
            if current_time - last_check_time >= check_interval:
                status = self.check_task_status(prompt_id)
                elapsed = int(current_time - start_time)
                
                if status == 'completed':
                    print(f"\n✅ 任务已完成！ (用时: {elapsed}秒)")
                    return True
                elif status == 'running':
                    print(f"\r🔄 任务运行中... (已用时: {elapsed}秒)", end='', flush=True)
                elif status == 'not_found':
                    print(f"\n❌ 任务不存在或已被清理！")
                    return False
                elif status is None:
                    print(f"\n⚠️ 检查状态时出错")
                
                last_check_time = current_time
            
            time.sleep(1)
        
        print(f"\n⏰ 监控超时 ({timeout}秒)")
        return False

    def monitor_progress_only(self, prompt_id: str, timeout: int = 600, auto_download: bool = True, output_dir: str = "outputs") -> bool:
        """
        监控任务进度，并在完成后自动下载结果

        Args:
            prompt_id: 工作流ID
            timeout: 超时时间（秒）
            auto_download: 完成后是否自动下载结果
            output_dir: 输出目录

        Returns:
            是否成功完成
        """
        # 首先检查任务状态
        print(f"🔍 检查任务状态 - Prompt ID: {prompt_id}")
        task_status = self.check_task_status(prompt_id)

        if task_status == 'completed':
            print("✅ 任务已完成！")
            if auto_download:
                print("📥 开始下载输出文件...")
                return self.get_result_by_prompt_id(prompt_id, output_dir)
            return True
        elif task_status == 'not_found':
            print("❌ 任务不存在或已过期！")
            return False
        elif task_status == 'running':
            print("🔄 任务正在运行，使用轮询方式监控进度...")
        else:
            print("⚠️ 无法确定任务状态，使用轮询方式监控...")

        # 使用轮询方式监控，不依赖WebSocket
        try:
            success = self.poll_for_completion(prompt_id, timeout)

            if success:
                print(f"\n✅ 任务完成！")
                if auto_download:
                    print("📥 开始下载输出文件...")
                    # 保持连接状态继续下载
                    download_success = self.get_result_by_prompt_id(prompt_id, output_dir)
                    if download_success:
                        print(f"\n🎉 监控和下载全部完成！")
                        return True
                    else:
                        print(f"\n⚠️ 任务完成但下载失败")
                        return False
                return True
            else:
                print(f"\n❌ 任务失败或超时！")
                return False

        except Exception as e:
            print(f"\n❌ 监控异常: {e}")
            success = False
            return False
        finally:
            try:
                if not auto_download or not success:
                    self.disconnect()
            except:
                pass

    def get_results(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流执行结果"""
        try:
            url = f"http://{self.server_address}/history/{prompt_id}"
            with urllib.request.urlopen(url) as response:
                history = json.loads(response.read().decode('utf-8'))

                if prompt_id in history:
                    result = history[prompt_id]
                    print("获取执行结果成功")
                    return result
                else:
                    print("未找到执行结果")
                    return None

        except Exception as e:
            print(f"获取结果异常: {e}")
            return None

    def extract_output_files(self, result: Dict[str, Any]) -> Dict[str, list]:
        """从结果中提取输出文件信息"""
        output_files = {}

        if 'outputs' in result:
            for node_id, node_output in result['outputs'].items():
                files = []

                # 检查视频文件
                if 'videos' in node_output:
                    for video in node_output['videos']:
                        video_url = f"http://{self.server_address}/view?filename={video['filename']}&type={video['type']}"
                        files.append({
                            'type': 'video',
                            'filename': video['filename'],
                            'url': video_url,
                            'subfolder': video.get('subfolder', '')
                        })

                # 检查音频文件
                if 'audios' in node_output:
                    for audio in node_output['audios']:
                        audio_url = f"http://{self.server_address}/view?filename={audio['filename']}&type={audio['type']}"
                        files.append({
                            'type': 'audio',
                            'filename': audio['filename'],
                            'url': audio_url,
                            'subfolder': audio.get('subfolder', '')
                        })

                # 检查图像文件
                if 'images' in node_output:
                    for image in node_output['images']:
                        image_url = f"http://{self.server_address}/view?filename={image['filename']}&type={image['type']}"
                        files.append({
                            'type': 'image',
                            'filename': image['filename'],
                            'url': image_url,
                            'subfolder': image.get('subfolder', '')
                        })

                # 检查GIF文件
                if 'gifs' in node_output:
                    for gif in node_output['gifs']:
                        gif_url = f"http://{self.server_address}/view?filename={gif['filename']}&type={gif['type']}"
                        files.append({
                            'type': 'gif',
                            'filename': gif['filename'],
                            'url': gif_url,
                            'subfolder': gif.get('subfolder', '')
                        })

                if files:
                    output_files[node_id] = files

        return output_files

    def download_file(self, file_info: Dict[str, Any], save_path: str) -> bool:
        """下载生成的文件"""
        try:
            urllib.request.urlretrieve(file_info['url'], save_path)
            print(f"文件下载成功: {save_path}")
            return True
        except Exception as e:
            print(f"文件下载失败: {e}")
            return False

    def run_workflow(self, workflow_path: str, audio_path: str, video_path: str,
                    text_prompt: str, positive_prompt: str, negative_prompt: str = "",
                    output_dir: str = "outputs") -> Optional[str]:
        """
        运行完整的数字人生成工作流

        Args:
            workflow_path: 工作流配置文件路径
            audio_path: 音频文件路径
            video_path: 视频参考图像路径
            text_prompt: 文本提示
            positive_prompt: 正面提示词
            negative_prompt: 负面提示词
            output_dir: 输出目录

        Returns:
            成功时返回prompt_id，失败返回None
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 连接服务器
        if not self.connect():
            return None

        try:
            # 加载工作流配置
            workflow = self.load_workflow(workflow_path)
            if not workflow:
                return None

            # 上传音频文件
            if audio_path and os.path.exists(audio_path):
                uploaded_audio = self.upload_file(audio_path)
                if not uploaded_audio:
                    return None
                audio_path = uploaded_audio

            # 上传视频参考图像
            if video_path and os.path.exists(video_path):
                uploaded_video = self.upload_file(video_path)
                if not uploaded_video:
                    return None
                video_path = uploaded_video

            # 更新工作流参数
            updated_workflow = self.update_workflow_parameters(
                workflow, audio_path, video_path, text_prompt, positive_prompt, negative_prompt
            )

            # 提交工作流
            prompt_id = self.submit_workflow(updated_workflow)
            if not prompt_id:
                return None

            # 等待执行完成
            if not self.wait_for_completion(prompt_id, show_progress=True):
                return None

            # 获取结果
            result = self.get_results(prompt_id)
            if not result:
                return None

            # 提取并下载输出文件
            output_files = self.extract_output_files(result)
            if output_files:
                print(f"生成文件数量: {sum(len(files) for files in output_files.values())}")

                for node_id, files in output_files.items():
                    for file_info in files:
                        filename = file_info['filename']
                        save_path = os.path.join(output_dir, filename)

                        if self.download_file(file_info, save_path):
                            print(f"文件已保存: {save_path}")

            return prompt_id

        except Exception as e:
            print(f"工作流执行异常: {e}")
            return None
        finally:
            self.disconnect()

    def get_result_by_prompt_id(self, prompt_id: str, output_dir: str = "outputs") -> bool:
        """
        根据prompt_id获取执行结果并下载文件

        Args:
            prompt_id: 工作流ID
            output_dir: 输出目录

        Returns:
            是否成功获取结果
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 连接服务器
        if not self.connect():
            return False

        try:
            # 直接获取结果，不需要等待（任务已完成）
            print(f"获取执行结果，Prompt ID: {prompt_id}")
            result = self.get_results(prompt_id)
            if not result:
                print("获取结果失败")
                return False

            print(f"结果数据: {result.keys() if result else 'None'}")
            
            # 显示详细的outputs结构
            if 'outputs' in result:
                outputs = result['outputs']
                print(f"Outputs 结构: {outputs.keys() if outputs else 'Empty'}")
                for node_id, node_output in outputs.items():
                    print(f"节点 {node_id}: {list(node_output.keys())}")
                    if 'videos' in node_output:
                        print(f"  - videos: {node_output['videos']}")
                    if 'audios' in node_output:
                        print(f"  - audios: {node_output['audios']}")
                    if 'images' in node_output:
                        print(f"  - images: {node_output['images']}")
                    if 'gifs' in node_output:
                        print(f"  - gifs: {node_output['gifs']}")
            else:
                print("Result 中没有 'outputs' 字段")

            # 提取并下载输出文件
            output_files = self.extract_output_files(result)
            print(f"提取到的输出文件: {output_files}")
            
            if output_files:
                print(f"生成文件数量: {sum(len(files) for files in output_files.values())}")

                video_files = []
                audio_files = []
                image_files = []
                gif_files = []
                
                for node_id, files in output_files.items():
                    print(f"节点 {node_id} 的输出文件: {len(files)}个")
                    for file_info in files:
                        filename = file_info['filename']
                        file_type = file_info['type']
                        save_path = os.path.join(output_dir, filename)
                        
                        print(f"下载 {file_type} 文件: {filename}")
                        if self.download_file(file_info, save_path):
                            print(f"文件已保存: {save_path}")
                            if file_type == 'video':
                                video_files.append(save_path)
                            elif file_type == 'audio':
                                audio_files.append(save_path)
                            elif file_type == 'image':
                                image_files.append(save_path)
                            elif file_type == 'gif':
                                gif_files.append(save_path)
                        else:
                            print(f"文件下载失败: {filename}")

                if video_files:
                    print(f"\n🎥 视频文件生成完成！")
                    for video_file in video_files:
                        print(f"  - {video_file}")
                        
                if audio_files:
                    print(f"\n🎧 音频文件生成完成！")
                    for audio_file in audio_files:
                        print(f"  - {audio_file}")
                        
                if image_files:
                    print(f"\n🖼️ 图片文件生成完成！")
                    for image_file in image_files:
                        print(f"  - {image_file}")
                        
                if gif_files:
                    print(f"\n🎉 GIF动图文件生成完成！")
                    for gif_file in gif_files:
                        print(f"  - {gif_file}")
                        
                if not (video_files or audio_files or image_files or gif_files):
                    print("\n⚠️ 未找到任何可下载的文件")
            else:
                print("\n⚠️ 未找到任何输出文件")

            return True

        except Exception as e:
            print(f"获取结果异常: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """主函数 - 支持命令行参数"""
    parser = argparse.ArgumentParser(description="数字人生成工作流客户端")
    parser.add_argument("--mode", choices=["run", "get_result", "monitor"], default="run",
                       help="运行模式: run(运行工作流) | get_result(获取结果) | monitor(仅监控进度)")
    parser.add_argument("--server", default="127.0.0.1:6006",
                       help="ComfyUI服务器地址")
    parser.add_argument("--workflow", default="voice-video-04-api.json",
                       help="工作流配置文件路径")
    parser.add_argument("--audio", default="awoman2.mp3",
                       help="音频文件路径")
    parser.add_argument("--video", default="kaka2.png",
                       help="视频参考图像路径")
    parser.add_argument("--text", default="这个的速度为什么变快了",
                       help="文本提示")
    parser.add_argument("--positive", default="A woman passionately talking",
                       help="正面提示词")
    parser.add_argument("--negative",
                       default="bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards",
                       help="负面提示词")
    parser.add_argument("--output", default="outputs",
                       help="输出目录")
    parser.add_argument("--prompt_id",
                       help="指定要获取结果或监控的prompt_id")
    parser.add_argument("--timeout", type=int, default=600,
                       help="超时时间（秒），默认600秒")
    parser.add_argument("--no_download", action="store_true",
                       help="monitor模式下不自动下载结果")

    args = parser.parse_args()

    # 创建客户端
    client = DigitalHumanWorkflowClient(server_address=args.server)

    if args.mode == "run":
        # 运行工作流模式
        print("=== 开始运行数字人生成工作流 ===")
        print(f"工作流配置: {args.workflow}")
        print(f"音频文件: {args.audio}")
        print(f"图像文件: {args.video}")
        print(f"文本提示: {args.text}")
        print(f"正面提示词: {args.positive}")
        print(f"负面提示词: {args.negative}")
        print(f"输出目录: {args.output}")
        print(f"超时时间: {args.timeout}秒")
        print("=" * 50)

        prompt_id = client.run_workflow(
            workflow_path=args.workflow,
            audio_path=args.audio,
            video_path=args.video,
            text_prompt=args.text,
            positive_prompt=args.positive,
            negative_prompt=args.negative,
            output_dir=args.output
        )

        if prompt_id:
            print(f"\n✅ 数字人生成完成！")
            print(f"🎯 Prompt ID: {prompt_id}")
            print(f"💾 输出目录: {args.output}")
            print(f"\n💡 其他可用命令：")
            print(f"  • 重新获取结果: python run_workflow.py --mode get_result --prompt_id {prompt_id}")
            print(f"  • 仅监控进度: python run_workflow.py --mode monitor --prompt_id {prompt_id}")
        else:
            print("\n❌ 数字人生成失败！")

    elif args.mode == "get_result":
        # 获取结果模式
        if not args.prompt_id:
            print("❌ 错误：get_result模式需要提供 --prompt_id 参数")
            return

        print("=== 获取数字人生成结果 ===")
        print(f"Prompt ID: {args.prompt_id}")
        print(f"输出目录: {args.output}")
        print(f"超时时间: {args.timeout}秒")
        print("=" * 50)

        success = client.get_result_by_prompt_id(
            prompt_id=args.prompt_id,
            output_dir=args.output
        )

        if success:
            print(f"\n✅ 结果获取完成！")
            print(f"💾 输出目录: {args.output}")
        else:
            print(f"\n❌ 结果获取失败！")

    elif args.mode == "monitor":
        # 仅监控进度模式
        if not args.prompt_id:
            print("❌ 错误：monitor模式需要提供 --prompt_id 参数")
            return

        print("=== 监控数字人生成进度 ===")
        print(f"Prompt ID: {args.prompt_id}")
        print(f"超时时间: {args.timeout}秒")
        print("🔍 正在连接服务器并监控任务进度...")
        print("=" * 50)

        success = client.monitor_progress_only(
            prompt_id=args.prompt_id,
            timeout=args.timeout,
            auto_download=not args.no_download,
            output_dir=args.output
        )

        if success:
            if args.no_download:
                print(f"\n✅ 监控完成！任务已成功执行。")
                print(f"💡 如需下载结果，请运行: python run_workflow.py --mode get_result --prompt_id {args.prompt_id}")
            else:
                print(f"\n🎉 监控和下载全部完成！")
        else:
            print(f"\n❌ 监控结束！任务可能失败或超时。")


if __name__ == "__main__":
    main()