"""
数字人生成器 - 直接实现工作流逻辑
"""

import os
import time
import uuid
import json
import websocket
import urllib.request
import urllib.parse
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from character_manager_core import CharacterManager
from character_models import CharacterInfo, CharacterError, CharacterNotFoundError


class DigitalHumanWorkflowClient:
    """数字人工作流客户端 - 直接实现"""
    
    def __init__(self, server_address="127.0.0.1:6006"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """建立WebSocket连接"""
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            self.logger.info(f"已连接到服务器: {self.server_address}")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None

    def upload_file(self, file_path: str, file_type: str = "input") -> Optional[str]:
        """上传文件到ComfyUI服务器"""
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return None

        try:
            import requests

            self.logger.info(f"正在上传文件: {file_path}")
            file_size = os.path.getsize(file_path)
            self.logger.info(f"文件大小: {file_size} bytes")

            with open(file_path, 'rb') as f:
                files = {'image': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {
                    'type': file_type,
                    'subfolder': ''
                }

                upload_url = f"http://{self.server_address}/upload/image"
                self.logger.info(f"上传URL: {upload_url}")

                response = requests.post(
                    upload_url,
                    files=files,
                    data=data,
                    timeout=30
                )

                self.logger.info(f"HTTP状态码: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        self.logger.info(f"JSON响应: {result}")

                        if 'name' in result:
                            uploaded_name = result.get('name', os.path.basename(file_path))
                            self.logger.info(f"文件上传成功: {file_path} -> {uploaded_name}")
                            return uploaded_name
                        else:
                            error_msg = result.get('error', '未知错误')
                            self.logger.error(f"文件上传失败: {error_msg}")
                            return None
                    except ValueError as e:
                        self.logger.error(f"解析JSON响应失败: {e}")
                        return None
                else:
                    self.logger.error(f"HTTP请求失败: {response.status_code}")
                    return None

        except ImportError:
            self.logger.error("需要安装requests库: pip install requests")
            return None
        except Exception as e:
            self.logger.error(f"文件上传异常: {e}")
            return None

    def load_workflow(self, workflow_path: str) -> Optional[Dict[str, Any]]:
        """加载工作流配置文件"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            self.logger.info(f"工作流配置加载成功: {workflow_path}")
            return workflow
        except Exception as e:
            self.logger.error(f"工作流配置加载失败: {e}")
            return None

    def update_workflow_parameters(self, workflow: Dict[str, Any],
                                 audio_path: str, video_path: str,
                                 text_prompt: str, positive_prompt: str,
                                 negative_prompt: str = "") -> Dict[str, Any]:
        """更新工作流参数"""
        updated_workflow = workflow.copy()

        # 更新音频文件路径 (节点1)
        if audio_path:
            if "1" in updated_workflow:
                updated_workflow["1"]["inputs"]["audio"] = audio_path
                updated_workflow["1"]["inputs"]["audioUI"] = ""

        # 更新视频参考图像路径 (节点5)
        if video_path:
            if "5" in updated_workflow:
                updated_workflow["5"]["inputs"]["video"] = video_path

        # 更新文本提示 (节点3)
        if text_prompt:
            if "3" in updated_workflow:
                updated_workflow["3"]["inputs"]["multi_line_prompt"] = text_prompt

        # 更新正面提示词 (节点21)
        if positive_prompt:
            if "21" in updated_workflow:
                updated_workflow["21"]["inputs"]["positive_prompt"] = positive_prompt

        # 更新负面提示词 (节点21)
        if negative_prompt:
            if "21" in updated_workflow:
                updated_workflow["21"]["inputs"]["negative_prompt"] = negative_prompt

        return updated_workflow

    def submit_workflow_async(self, workflow_path: str, audio_path: str, video_path: str,
                             text_prompt: str, positive_prompt: str, negative_prompt: str = "") -> Optional[str]:
        """异步提交工作流到服务器"""
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
        return self.submit_workflow(updated_workflow)
    
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
                    self.logger.info(f"工作流提交成功，Prompt ID: {actual_prompt_id}")
                    return actual_prompt_id
                else:
                    self.logger.error(f"工作流提交失败: {result}")
                    return None

        except Exception as e:
            self.logger.error(f"工作流提交异常: {e}")
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 600, show_progress: bool = True) -> bool:
        """等待工作流执行完成"""
        if not self.ws:
            self.logger.error("WebSocket未连接")
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
                                        progress_text = self._format_progress_display(node_status)
                                        print(f"\r🔄 执行中: {progress_text}", end='', flush=True)

                        elif data.get('type') == 'progress':
                            progress = data.get('data', {})
                            value = progress.get('value', 0)
                            max_value = progress.get('max', 1)
                            if max_value > 0:
                                percentage = (value / max_value) * 100
                                if show_progress and time.time() - last_progress_time > 0.5:
                                    print(f"\r📊 进度: {percentage:.1f}% ({value}/{max_value})", end='', flush=True)
                                    last_progress_time = time.time()

                        elif data.get('type') == 'error':
                            error_data = data.get('data', {})
                            print(f"\n❌ 执行错误: {error_data.get('exception_message', '未知错误')}")
                            return False

                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    print(f"\n⚠️ 接收消息异常: {e}")
                    break

            print(f"\n⏰ 等待超时 ({timeout}秒)")
            return False

        except Exception as e:
            self.logger.error(f"等待执行异常: {e}")
            return False

    def _format_progress_display(self, node_status: Dict[str, str]) -> str:
        """格式化进度显示文本"""
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

    def get_results(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流执行结果"""
        try:
            url = f"http://{self.server_address}/history/{prompt_id}"
            with urllib.request.urlopen(url) as response:
                history = json.loads(response.read().decode('utf-8'))

                if prompt_id in history:
                    result = history[prompt_id]
                    self.logger.info("获取执行结果成功")
                    return result
                else:
                    self.logger.error("未找到执行结果")
                    return None

        except Exception as e:
            self.logger.error(f"获取结果异常: {e}")
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

                if files:
                    output_files[node_id] = files

        return output_files

    def download_file(self, file_info: Dict[str, Any], save_path: str) -> bool:
        """下载生成的文件"""
        try:
            urllib.request.urlretrieve(file_info['url'], save_path)
            self.logger.info(f"文件下载成功: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"文件下载失败: {e}")
            return False

    def run_workflow(self, workflow_path: str, audio_path: str, video_path: str,
                    text_prompt: str, positive_prompt: str, negative_prompt: str = "",
                    output_dir: str = "outputs") -> Optional[str]:
        """运行完整的数字人生成工作流"""
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
            self.logger.error(f"工作流执行异常: {e}")
            return None
        finally:
            self.disconnect()


class DigitalHumanGenerator:
    """数字人生成器 - 直接包含工作流逻辑"""
    
    def __init__(self, server_address: str = "127.0.0.1:6006", 
                 characters_dir: str = "characters",
                 output_dir: str = "outputs"):
        self.character_manager = CharacterManager(characters_dir)
        self.workflow_client = DigitalHumanWorkflowClient(server_address)
        self.default_workflow = "voice-video-04-api.json"
        self.output_dir = output_dir
        self.server_address = server_address
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_video_async(self, character_name: str, text: str,
                          positive_prompt: Optional[str] = None,
                          negative_prompt: Optional[str] = None,
                          workflow_path: Optional[str] = None) -> Optional[str]:
        """异步生成数字人视频（不等待完成）"""
        try:
            print(f"🚀 异步提交数字人视频生成任务...")
            print(f"📝 角色: {character_name}")
            print(f"📝 文本: {text}")
            
            # 预验证角色
            if not self.validate_character_before_generation(character_name):
                return None
            
            # 加载角色信息
            character_info = self.character_manager.load_character(character_name)
            
            # 显示角色信息
            self._print_character_info(character_info)
            
            # 检查服务器连接
            print(f"🔌 检查服务器连接...")
            if not self.workflow_client.connect():
                print(f"❌ 无法连接到服务器: {self.workflow_client.server_address}")
                return None
            
            try:
                # 设置工作流参数
                workflow_params = self.setup_character_workflow(
                    character_info, text, positive_prompt, negative_prompt
                )
                
                # 使用指定的工作流文件或默认工作流
                workflow_file = workflow_path or self.default_workflow
                
                # 检查工作流文件是否存在
                if not os.path.exists(workflow_file):
                    print(f"❌ 工作流文件不存在: {workflow_file}")
                    return None
                
                print(f"⚙️  使用工作流: {workflow_file}")
                
                # 提交工作流（异步，不等待完成）
                print(f"🚀 异步提交生成任务...")
                prompt_id = self.workflow_client.submit_workflow_async(
                    workflow_path=workflow_file,
                    audio_path=workflow_params['audio_path'],
                    video_path=workflow_params['video_path'],
                    text_prompt=workflow_params['text_prompt'],
                    positive_prompt=workflow_params['positive_prompt'],
                    negative_prompt=workflow_params['negative_prompt']
                )
                
                if prompt_id:
                    print(f"✅ 异步任务已提交")
                    print(f"🎯 Prompt ID: {prompt_id}")
                    print(f"💡 使用以下命令监控进度: python character_manager.py monitor {prompt_id}")
                else:
                    print("❌ 异步任务提交失败")
                
                return prompt_id
                
            finally:
                # 确保断开连接
                try:
                    self.workflow_client.disconnect()
                except:
                    pass
            
        except CharacterNotFoundError as e:
            print(f"❌ 角色不存在: {e.character_name}")
            return None
        except Exception as e:
            print(f"❌ 异步提交过程中发生错误: {e}")
            return None
    
    def generate_video(self, character_name: str, text: str,
                      positive_prompt: Optional[str] = None,
                      negative_prompt: Optional[str] = None,
                      workflow_path: Optional[str] = None,
                      timeout: int = 600) -> Optional[str]:
        """生成数字人视频的主要接口"""
        try:
            print(f"🎭 开始生成数字人视频...")
            print(f"📝 角色: {character_name}")
            print(f"📝 文本: {text}")
            
            # 预验证角色
            if not self.validate_character_before_generation(character_name):
                return None
            
            # 加载角色信息
            character_info = self.character_manager.load_character(character_name)
            
            # 显示角色信息
            self._print_character_info(character_info)
            
            # 检查服务器连接
            print(f"🔌 检查服务器连接...")
            if not self.workflow_client.connect():
                print(f"❌ 无法连接到服务器: {self.workflow_client.server_address}")
                print(f"💡 请确保 ComfyUI 服务器正在运行")
                return None
            
            try:
                # 设置工作流参数
                workflow_params = self.setup_character_workflow(
                    character_info, text, positive_prompt, negative_prompt
                )
                
                # 使用指定的工作流文件或默认工作流
                workflow_file = workflow_path or self.default_workflow
                
                # 检查工作流文件是否存在
                if not os.path.exists(workflow_file):
                    print(f"❌ 工作流文件不存在: {workflow_file}")
                    print(f"💡 请确保工作流配置文件存在")
                    return None
                
                print(f"⚙️  使用工作流: {workflow_file}")
                
                # 运行工作流
                print(f"🚀 提交生成任务...")
                prompt_id = self.workflow_client.run_workflow(
                    workflow_path=workflow_file,
                    audio_path=workflow_params['audio_path'],
                    video_path=workflow_params['video_path'],
                    text_prompt=workflow_params['text_prompt'],
                    positive_prompt=workflow_params['positive_prompt'],
                    negative_prompt=workflow_params['negative_prompt'],
                    output_dir=self.output_dir
                )
                
                if prompt_id:
                    print(f"✅ 数字人视频生成任务已提交")
                    print(f"🎯 Prompt ID: {prompt_id}")
                    print(f"💾 输出目录: {self.output_dir}")
                    
                    # 生成输出文件名模式
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    expected_filename = f"{character_name}_{timestamp}.mp4"
                    print(f"📁 预期输出文件: {expected_filename}")
                    
                    print(f"\n💡 其他可用命令:")
                    print(f"  • 监控进度: python character_manager.py monitor {prompt_id}")
                    print(f"  • 获取结果: python character_manager.py result {prompt_id}")
                    print(f"  • 重新生成: python character_manager.py generate {character_name} \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
                    
                else:
                    print("❌ 数字人视频生成失败")
                    print(f"💡 请检查服务器状态和工作流配置")
                
                return prompt_id
                
            finally:
                # 确保断开连接
                try:
                    self.workflow_client.disconnect()
                except:
                    pass
            
        except CharacterNotFoundError as e:
            print(f"❌ 角色不存在: {e.character_name}")
            self._suggest_available_characters()
            self._print_character_creation_help()
            return None
        except Exception as e:
            print(f"❌ 生成过程中发生错误: {e}")
            self.logger.error(f"生成数字人视频失败: {e}", exc_info=True)
            self._print_troubleshooting_help()
            return None
    
    def setup_character_workflow(self, character_info: CharacterInfo, text: str,
                               positive_prompt: Optional[str] = None,
                               negative_prompt: Optional[str] = None) -> Dict[str, Any]:
        """为特定角色设置工作流参数"""
        # 获取角色的默认提示词
        final_positive_prompt = positive_prompt or character_info.get_positive_prompt()
        final_negative_prompt = negative_prompt or character_info.get_negative_prompt()
        
        # 构建基础参数
        params = {
            'audio_path': character_info.audio_path,
            'video_path': character_info.visual_path,
            'text_prompt': text,
            'positive_prompt': final_positive_prompt,
            'negative_prompt': final_negative_prompt,
            'character_name': character_info.name,
            'visual_type': character_info.visual_type,
        }
        
        self.logger.info(f"工作流参数设置完成: {character_info.name}")
        return params
    
    def monitor_progress_only(self, prompt_id: str, timeout: int = 600, auto_download: bool = True, output_dir: str = "outputs") -> bool:
        """监控任务进度，并在完成后自动下载结果"""
        print(f"🔍 检查任务状态 - Prompt ID: {prompt_id}")
        
        # 首先检查任务状态
        try:
            url = f"http://{self.server_address}/history/{prompt_id}"
            with urllib.request.urlopen(url) as response:
                history = json.loads(response.read().decode('utf-8'))
                if prompt_id in history:
                    print("✅ 任务已完成！")
                    if auto_download:
                        print("📥 开始下载输出文件...")
                        return self.get_result_by_prompt_id(prompt_id, output_dir)
                    return True
        except:
            pass
        
        # 检查队列状态
        try:
            queue_url = f"http://{self.server_address}/queue"
            with urllib.request.urlopen(queue_url) as response:
                queue_data = json.loads(response.read().decode('utf-8'))
                
                # 检查正在执行的任务
                for item in queue_data.get('queue_running', []):
                    if len(item) > 1 and item[1] == prompt_id:
                        print("🔄 任务正在运行，开始监控...")
                        return self.poll_for_completion(prompt_id, timeout, auto_download, output_dir)
                
                # 检查等待队列
                for item in queue_data.get('queue_pending', []):
                    if len(item) > 1 and item[1] == prompt_id:
                        print("🔄 任务在等待队列中，开始监控...")
                        return self.poll_for_completion(prompt_id, timeout, auto_download, output_dir)
        except:
            pass
        
        print("❌ 任务不存在或已过期！")
        return False
    
    def poll_for_completion(self, prompt_id: str, timeout: int = 600, auto_download: bool = True, output_dir: str = "outputs") -> bool:
        """使用轮询方式监控任务完成"""
        start_time = time.time()
        last_check_time = 0
        check_interval = 5
        
        print("=" * 60)
        
        while time.time() - start_time < timeout:
            current_time = time.time()
            
            # 每隔一段时间检查一次状态
            if current_time - last_check_time >= check_interval:
                try:
                    # 检查历史记录
                    url = f"http://{self.server_address}/history/{prompt_id}"
                    with urllib.request.urlopen(url) as response:
                        history = json.loads(response.read().decode('utf-8'))
                        if prompt_id in history:
                            print(f"\n✅ 任务已完成！ (用时: {int(current_time - start_time)}秒)")
                            if auto_download:
                                print("📥 开始下载输出文件...")
                                return self.get_result_by_prompt_id(prompt_id, output_dir)
                            return True
                except:
                    pass
                
                elapsed = int(current_time - start_time)
                print(f"\r🔄 任务运行中... (已用时: {elapsed}秒)", end='', flush=True)
                
                last_check_time = current_time
            
            time.sleep(1)
        
        print(f"\n⏰ 监控超时 ({timeout}秒)")
        return False
    
    def get_result_by_prompt_id(self, prompt_id: str, output_dir: str = "outputs") -> bool:
        """根据prompt_id获取执行结果并下载文件"""
        try:
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
            else:
                print("Result 中没有 'outputs' 字段")

            # 提取并下载输出文件
            output_files = self.extract_output_files(result)
            print(f"提取到的输出文件: {output_files}")
            
            if output_files:
                print(f"生成文件数量: {sum(len(files) for files in output_files.values())}")

                video_files = []
                audio_files = []
                
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
                        
                if not (video_files or audio_files):
                    print("\n⚠️ 未找到任何可下载的文件")
            else:
                print("\n⚠️ 未找到任何输出文件")

            return True

        except Exception as e:
            print(f"获取结果异常: {e}")
            return False
    
    def _print_character_info(self, character_info: CharacterInfo):
        """打印角色信息"""
        print(f"🎭 角色信息:")
        print(f"   名称: {character_info.name}")
        print(f"   音频: {Path(character_info.audio_path).name}")
        print(f"   视觉: {Path(character_info.visual_path).name} ({character_info.visual_type})")
        
        if character_info.config.get('description'):
            print(f"   描述: {character_info.config['description']}")
        
        if character_info.config.get('tags'):
            print(f"   标签: {', '.join(character_info.config['tags'])}")
    
    def _suggest_available_characters(self):
        """建议可用的角色"""
        try:
            characters = self.character_manager.list_characters()
            if characters:
                print(f"💡 可用的角色:")
                for char in characters:
                    print(f"   - {char}")
            else:
                print(f"💡 当前没有可用的角色")
                print(f"   请在 '{self.character_manager.characters_dir}' 目录下创建角色文件夹")
        except Exception as e:
            print(f"💡 无法获取角色列表: {e}")
    
    def get_character_suggestions(self, partial_name: str = "") -> List[str]:
        """获取角色建议（支持模糊匹配）"""
        try:
            characters = self.character_manager.list_characters()
            if not partial_name:
                return characters
            
            # 简单的模糊匹配
            partial_lower = partial_name.lower()
            suggestions = []
            
            for char in characters:
                if partial_lower in char.lower():
                    suggestions.append(char)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"获取角色建议失败: {e}")
            return []
    
    def validate_character_before_generation(self, character_name: str) -> bool:
        """在生成前验证角色"""
        try:
            character_info = self.character_manager.load_character(character_name)
            
            # 检查文件是否存在
            if not os.path.exists(character_info.audio_path):
                print(f"❌ 音频文件不存在: {character_info.audio_path}")
                return False
            
            if not os.path.exists(character_info.visual_path):
                print(f"❌ 视觉文件不存在: {character_info.visual_path}")
                return False
            
            # 检查文件大小
            from character_models import get_file_size_mb
            audio_size = get_file_size_mb(character_info.audio_path)
            visual_size = get_file_size_mb(character_info.visual_path)
            
            if audio_size > 100:
                print(f"⚠️ 音频文件较大: {audio_size:.1f}MB")
            
            if visual_size > 50:
                print(f"⚠️ 视觉文件较大: {visual_size:.1f}MB")
            
            print(f"✅ 角色验证通过: {character_name}")
            return True
            
        except CharacterError as e:
            print(f"❌ 角色验证失败: {e}")
            return False
    
    def _print_character_creation_help(self):
        """打印角色创建帮助"""
        print(f"\n💡 角色创建帮助:")
        print(f"1. 在 '{self.character_manager.characters_dir}' 目录下创建角色文件夹")
        print(f"2. 每个角色文件夹需要包含:")
        print(f"   • 参考音频文件 (.mp3, .wav, .m4a)")
        print(f"   • 参考图片文件 (.jpg, .png, .webp) 或 视频文件 (.mp4, .avi)")
        print(f"3. 可选: 创建 config.json 配置文件")
        print(f"4. 示例: python character_manager.py init --create-example --example-name \"我的角色\"")
    
    def _print_troubleshooting_help(self):
        """打印故障排除帮助"""
        print(f"\n🔧 故障排除:")
        print(f"1. 确保服务器正在运行: {self.workflow_client.server_address}")
        print(f"2. 检查网络连接")
        print(f"3. 验证工作流文件存在: {self.default_workflow}")
        print(f"4. 检查输出目录权限: {self.output_dir}")
        print(f"5. 查看详细日志: python character_manager.py --verbose <command>")
        print(f"6. 清除缓存: python character_manager.py cache --clear")