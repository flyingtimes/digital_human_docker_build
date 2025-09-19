以下是一个通过api调用工作流的示例程序：
```
import json  
import websocket  
import urllib.request  
import uuid  
from io import BytesIO  
  
class TextAudioToVideoClient:  
    def __init__(self, server_address="127.0.0.1:8188"):  
        self.server_address = server_address  
        self.client_id = str(uuid.uuid4())  
          
    def connect(self):  
        """建立WebSocket连接"""  
        self.ws = websocket.WebSocket()  
        self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")  
      
    def upload_audio(self, audio_file_path):  
        """上传音频文件到ComfyUI"""  
        # 这里需要实现音频文件上传逻辑  
        # 参考 upload_audio_to_comfyapi 函数  
        pass  
      
    def create_workflow(self, text_prompt, audio_url):  
        """创建文字+音频到视频的工作流"""  
        workflow = {  
            # 根据你的具体需求构建工作流JSON  
            # 可以使用Kling唇语同步或其他视频生成节点  
            "1": {  
                "class_type": "KlingLipSyncTextToVideoNode",  
                "inputs": {  
                    "text": text_prompt,  
                    "audio_url": audio_url,  
                    # 其他参数...  
                }  
            }  
        }  
        return workflow  
      
    def submit_and_wait(self, workflow):  
        """提交工作流并等待完成"""  
        prompt_id = str(uuid.uuid4())  
          
        # 提交工作流  
        p = {"prompt": workflow, "client_id": self.client_id, "prompt_id": prompt_id}  
        data = json.dumps(p).encode('utf-8')  
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)  
        urllib.request.urlopen(req)  
          
        # 等待执行完成  
        while True:  
            out = self.ws.recv()  
            if isinstance(out, str):  
                message = json.loads(out)  
                if message['type'] == 'executing':  
                    data = message['data']  
                    if data['node'] is None and data['prompt_id'] == prompt_id:  
                        break  
          
        # 获取结果  
        return self.get_results(prompt_id)  
      
    def get_results(self, prompt_id):  
        """获取生成的视频结果"""  
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:  
            history = json.loads(response.read())[prompt_id]  
          
        # 提取视频文件  
        for node_id in history['outputs']:  
            node_output = history['outputs'][node_id]  
            if 'videos' in node_output:  
                for video in node_output['videos']:  
                    # 下载视频文件  
                    video_url = f"http://{self.server_address}/view?filename={video['filename']}&type={video['type']}"  
                    return video_url  
          
        return None
```