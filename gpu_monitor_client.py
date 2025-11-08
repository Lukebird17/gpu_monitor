#!/usr/bin/env python3
"""
GPU监控客户端 - 收集本地GPU信息并发送到服务端
运行方式: python gpu_monitor_client.py --server http://your-server:5000 --name my-server
"""

import subprocess
import json
import requests
import time
import socket
import argparse
from datetime import datetime
import xml.etree.ElementTree as ET

def get_hostname():
    """获取主机名"""
    return socket.gethostname()

def parse_gpu_info():
    """使用nvidia-smi获取GPU信息"""
    try:
        # 使用XML格式获取详细信息
        cmd = ['nvidia-smi', '-q', '-x']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"错误: nvidia-smi命令执行失败")
            return None
        
        # 解析XML
        root = ET.fromstring(result.stdout)
        gpus = []
        
        for i, gpu in enumerate(root.findall('gpu')):
            gpu_info = {
                'index': i,
                'name': gpu.find('product_name').text if gpu.find('product_name') is not None else 'Unknown',
                'temperature': gpu.find('.//temperature/gpu_temp').text.replace(' C', '') if gpu.find('.//temperature/gpu_temp') is not None else 'N/A',
                'utilization': gpu.find('.//utilization/gpu_util').text.replace(' %', '') if gpu.find('.//utilization/gpu_util') is not None else '0',
                'memory_used': gpu.find('.//fb_memory_usage/used').text if gpu.find('.//fb_memory_usage/used') is not None else 'N/A',
                'memory_total': gpu.find('.//fb_memory_usage/total').text if gpu.find('.//fb_memory_usage/total') is not None else 'N/A',
                'power_draw': gpu.find('.//power_readings/power_draw').text if gpu.find('.//power_readings/power_draw') is not None else 'N/A',
                'power_limit': gpu.find('.//power_readings/power_limit').text if gpu.find('.//power_readings/power_limit') is not None else 'N/A',
                'processes': []
            }
            
            # 计算显存使用百分比
            try:
                memory_used = float(gpu.find('.//fb_memory_usage/used').text.split()[0])
                memory_total = float(gpu.find('.//fb_memory_usage/total').text.split()[0])
                gpu_info['memory_percent'] = f"{(memory_used / memory_total * 100):.1f}"
            except:
                gpu_info['memory_percent'] = '0'
            
            # 获取进程信息
            processes = gpu.find('.//processes')
            if processes is not None:
                for process in processes.findall('process_info'):
                    proc_info = {
                        'pid': process.find('pid').text if process.find('pid') is not None else 'N/A',
                        'name': process.find('process_name').text if process.find('process_name') is not None else 'Unknown',
                        'memory': process.find('used_memory').text if process.find('used_memory') is not None else 'N/A'
                    }
                    gpu_info['processes'].append(proc_info)
            
            gpus.append(gpu_info)
        
        return gpus
    
    except subprocess.TimeoutExpired:
        print("错误: nvidia-smi命令超时")
        return None
    except FileNotFoundError:
        print("错误: 未找到nvidia-smi命令，请确保已安装NVIDIA驱动")
        return None
    except Exception as e:
        print(f"错误: 解析GPU信息失败 - {str(e)}")
        return None

def send_data_to_server(server_url, server_name, gpu_data):
    """发送GPU数据到服务端"""
    try:
        payload = {
            'server_name': server_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gpus': gpu_data
        }
        
        response = requests.post(
            f"{server_url}/api/update",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"警告: 服务器返回错误状态码 {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到服务器 {server_url}")
        return False
    except requests.exceptions.Timeout:
        print(f"错误: 连接服务器超时")
        return False
    except Exception as e:
        print(f"错误: 发送数据失败 - {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='GPU监控客户端')
    parser.add_argument('--server', type=str, required=True, 
                       help='服务端地址，例如: http://192.168.1.100:5000')
    parser.add_argument('--name', type=str, default=None,
                       help='服务器名称 (默认使用主机名)')
    parser.add_argument('--interval', type=int, default=5,
                       help='更新间隔（秒）(默认: 5)')
    args = parser.parse_args()
    
    server_name = args.name if args.name else get_hostname()
    
    print(f"===========================================")
    print(f"GPU监控客户端启动")
    print(f"服务器名称: {server_name}")
    print(f"目标服务端: {args.server}")
    print(f"更新间隔: {args.interval}秒")
    print(f"===========================================")
    print()
    
    consecutive_failures = 0
    max_failures = 5
    
    while True:
        try:
            # 获取GPU信息
            gpu_data = parse_gpu_info()
            
            if gpu_data is None:
                print("⚠️  无法获取GPU信息，等待下次尝试...")
                time.sleep(args.interval)
                continue
            
            # 发送到服务端
            success = send_data_to_server(args.server, server_name, gpu_data)
            
            if success:
                consecutive_failures = 0
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"✅ [{current_time}] 数据发送成功 - {len(gpu_data)} 个GPU")
            else:
                consecutive_failures += 1
                print(f"❌ 数据发送失败 (连续失败: {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    print(f"⚠️  连续失败{max_failures}次，请检查网络连接和服务端状态")
                    consecutive_failures = 0  # 重置计数器，继续尝试
            
        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在退出...")
            break
        except Exception as e:
            print(f"❌ 发生未预期的错误: {str(e)}")
        
        # 等待指定间隔
        time.sleep(args.interval)

if __name__ == '__main__':
    main()

