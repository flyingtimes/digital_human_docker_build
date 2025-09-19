以下是获取一个prompt_id任务的进展信息的示例程序：
```
class ProgressMonitor:  
    def __init__(self, server_address="127.0.0.1:6006"):  
        self.server_address = server_address  
        self.client_id = str(uuid.uuid4())  
        self.progress_data = {}  
      
    def connect(self):  
        self.ws = websocket.WebSocket()  
        self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")  
      
    def monitor_progress(self, prompt_id):  
        while True:  
            out = self.ws.recv()  
            if isinstance(out, str):  
                message = json.loads(out)  
                  
                if message['type'] == 'progress_state':  
                    data = message['data']  
                    if data['prompt_id'] == prompt_id:  
                        nodes = data['nodes']  
                        overall_progress = self.calculate_progress(nodes)  
                        print(f"Progress: {overall_progress:.1%}")  
                          
                elif message['type'] == 'executing':  
                    data = message['data']  
                    if data['prompt_id'] == prompt_id and data['node'] is None:  
                        print("Execution completed!")  
                        break  
      
    def calculate_progress(self, nodes):  
        # 实现进度计算逻辑  
        pass
```