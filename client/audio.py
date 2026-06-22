"""
音频管理模块 - 处理麦克风录音和扬声器播放
"""

import numpy as np
import pyaudio
import threading
import queue
from typing import Optional, Callable


class AudioManager:
    """音频管理器"""
    
    def __init__(self, config: dict):
        """初始化音频管理器"""
        self.sample_rate = config.get('sample_rate', 16000)
        self.channels = config.get('channels', 1)
        self.chunk_size = config.get('chunk_size', 1024)
        self.device_index = config.get('device_index', -1)
        
        self.pa = pyaudio.PyAudio()
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.record_thread = None
        
    def get_available_devices(self):
        """获取可用的音频设备"""
        devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'channels': info['maxInputChannels']
            })
        return devices
    
    def start_recording(self) -> queue.Queue:
        """开始录音"""
        if self.is_recording:
            return self.audio_queue
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.daemon = True
        self.record_thread.start()
        
        return self.audio_queue
    
    def _record_audio(self):
        """录音线程"""
        try:
            stream = self.pa.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index if self.device_index >= 0 else None,
                frames_per_buffer=self.chunk_size
            )
            
            print("[*] 开始录音...")
            
            while self.is_recording:
                try:
                    data = stream.read(self.chunk_size)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    self.audio_queue.put(audio_data)
                except Exception as e:
                    print(f"[!] 录音错误: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            print("[✓] 录音结束")
            
        except Exception as e:
            print(f"[✗] 打开音频流失败: {e}")
    
    def stop_recording(self) -> np.ndarray:
        """停止录音并返回音频数据"""
        self.is_recording = False
        
        if self.record_thread:
            self.record_thread.join(timeout=2)
        
        # 收集所有音频数据
        audio_data = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                audio_data.append(chunk)
            except queue.Empty:
                break
        
        if audio_data:
            return np.concatenate(audio_data)
        else:
            return np.array([])
    
    def play_audio(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """播放音频"""
        try:
            stream = self.pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            # 确保音频数据是float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 归一化（防止超限）
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            
            stream.write(audio_data.tobytes())
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"[!] 播放音频失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.is_recording:
            self.stop_recording()
        self.pa.terminate()
