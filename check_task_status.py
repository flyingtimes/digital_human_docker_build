#!/usr/bin/env python3
"""
简单的任务状态检查脚本
"""

import json
import urllib.request
import time
import sys

def check_task_status(server_address, prompt_id):
    """检查任务状态"""
    try:
        # 检查历史记录
        url = f"http://{server_address}/history/{prompt_id}"
        with urllib.request.urlopen(url) as response:
            history = json.loads(response.read().decode('utf-8'))
            if prompt_id in history:
                return 'completed', history[prompt_id]
        
        # 检查队列
        queue_url = f"http://{server_address}/queue"
        with urllib.request.urlopen(queue_url) as response:
            queue_data = json.loads(response.read().decode('utf-8'))
            
            # 检查正在执行的任务
            for item in queue_data.get('queue_running', []):
                if len(item) > 1 and item[1] == prompt_id:
                    return 'running', None
            
            # 检查等待队列
            for item in queue_data.get('queue_pending', []):
                if len(item) > 1 and item[1] == prompt_id:
                    return 'pending', None
        
        return 'not_found', None
    except Exception as e:
        return 'error', str(e)

def monitor_task(server_address, prompt_id, timeout=600):
    """监控任务进度"""
    start_time = time.time()
    last_check_time = 0
    
    print(f"🔍 开始监控任务 - Prompt ID: {prompt_id}")
    print("=" * 60)
    
    while time.time() - start_time < timeout:
        current_time = time.time()
        
        # 每5秒检查一次状态
        if current_time - last_check_time >= 5:
            status, result = check_task_status(server_address, prompt_id)
            elapsed = int(current_time - start_time)
            
            if status == 'completed':
                print(f"\n✅ 任务完成！ (用时: {elapsed}秒)")
                
                # 显示输出文件信息
                if result and 'outputs' in result:
                    print("📁 生成的文件：")
                    for node_id, node_output in result['outputs'].items():
                        if 'videos' in node_output:
                            for video in node_output['videos']:
                                print(f"  🎥 视频: {video['filename']}")
                        if 'audios' in node_output:
                            for audio in node_output['audios']:
                                print(f"  🎵 音频: {audio['filename']}")
                        if 'images' in node_output:
                            for image in node_output['images']:
                                print(f"  🖼️ 图片: {image['filename']}")
                
                return True
                
            elif status == 'running':
                print(f"\r🔄 任务运行中... (已用时: {elapsed}秒)", end='', flush=True)
                
            elif status == 'pending':
                print(f"\r⏳ 任务等待中... (已用时: {elapsed}秒)", end='', flush=True)
                
            elif status == 'not_found':
                print(f"\n❌ 任务不存在或已被清理！")
                return False
                
            elif status == 'error':
                print(f"\n❌ 检查状态时出错: {result}")
                return False
            
            last_check_time = current_time
        
        time.sleep(1)
    
    print(f"\n⏰ 监控超时 ({timeout}秒)")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_task_status.py <prompt_id>")
        sys.exit(1)
    
    server_address = "127.0.0.1:6006"
    prompt_id = sys.argv[1]
    
    print(f"服务器地址: {server_address}")
    print(f"任务ID: {prompt_id}")
    print("-" * 50)
    
    success = monitor_task(server_address, prompt_id)
    sys.exit(0 if success else 1)
