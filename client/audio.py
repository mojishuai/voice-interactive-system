"""
音频管理模块 - 处理音频录制、播放、设备管理
支持实时录音、音频处理、多设备选择
"""

import numpy as np
import pyaudio
import wave
from typing import Optional, List, Callable, Dict
import threading
import logging
from collections import deque
import time

logger = logging.getLogger(__name__)


class AudioManager:
    """音频管理类"""
    
    def __init__(self, config: Dict):
        """
        初始化音频管理器
        
        Args:
            config: 音频配置字典
        """
        self.config = config
        self.sample_rate = config.get('sample_rate', 16000)
        self.channels = config.get('channels', 1)
        self.chunk_size = config.get('chunk_size', 1024)
        self.device_index = config.get('device_index', -1)
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_buffer = deque(maxlen=self.sample_rate * 30)  # 最多30秒
        self.callback = None
        self.record_thread = None
        
        logger.info(f"音频管理器初始化: 采样率={self.sample_rate}Hz, 通道={self.channels}")
        self._print_devices()
    
    def _print_devices(self):
        """打印可用的音频设备"""
        logger.info("可用音频设备:")
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            logger.info(f"  [{i}] {info['name']} - 输入:{info['maxInputChannels']} 输出:{info['maxOutputChannels']}")
    
    def list_devices(self) -> List[Dict]:
        """列出所有音频设备"""
        devices = []
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'input_channels': info['maxInputChannels'],
                'output_channels': info['maxOutputChannels']
            })
        return devices
    
    def set_device(self, device_index: int):
        """设置音频设备"""
        self.device_index = device_index
        logger.info(f"设置音频设备: {device_index}")
    
    def start_recording(self, callback: Optional[Callable] = None):
        """
        开始录音
        
        Args:
            callback: 录音回调函数，接收音频数据
        """
        if self.is_recording:
            logger.warning("已在录音中")
            return
        
        self.callback = callback
        self.is_recording = True
        self.audio_buffer.clear()
        
        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index if self.device_index >= 0 else None,
                frames_per_buffer=self.chunk_size
            )
            
            # 在后台线程中进行录音
            self.record_thread = threading.Thread(target=self._record_thread)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            logger.info("录音已开始")
        except Exception as e:
            logger.error(f"录音启动失败: {e}")
            self.is_recording = False
    
    def _record_thread(self):
        """录音线程"""
        try:
            while self.is_recording:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    self.audio_buffer.extend(audio_data)
                    
                    if self.callback:
                        self.callback(audio_data)
                except Exception as e:
                    logger.error(f"读取音频数据失败: {e}")
                    break
        except Exception as e:
            logger.error(f"录音线程异常: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.is_recording = False
    
    def stop_recording(self) -> np.ndarray:
        """
        停止录音
        
        Returns:
            录音的音频数据
        """
        if not self.is_recording:
            logger.warning("未在录音中")
            return np.array([])
        
        self.is_recording = False
        
        # 等待录音线程结束
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=2.0)
        
        audio_data = np.array(list(self.audio_buffer), dtype=np.float32)
        logger.info(f"录音已停止，收集了 {len(audio_data)} 样本")
        
        return audio_data
    
    def play_audio(self, audio_data: np.ndarray, sample_rate: Optional[int] = None):
        """
        播放音频
        
        Args:
            audio_data: 音频数据 (numpy array)
            sample_rate: 采样率
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # 将音频数据转换为字节
            audio_bytes = audio_data.astype(np.float32).tobytes()
            
            # 创建播放流
            stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=sample_rate,
                output=True,
                output_device_index=self.device_index if self.device_index >= 0 else None
            )
            
            # 播放音频
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()
            
            logger.info(f"播放音频: {len(audio_data)} 样本")
        except Exception as e:
            logger.error(f"音频播放失败: {e}")
    
    def save_audio(self, audio_data: np.ndarray, file_path: str, 
                   sample_rate: Optional[int] = None):
        """
        保存音频文件
        
        Args:
            audio_data: 音频数据
            file_path: 文件路径
            sample_rate: 采样率
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            with wave.open(file_path, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            logger.info(f"音频已保存: {file_path}")
        except Exception as e:
            logger.error(f"保存音频失败: {e}")
    
    def load_audio(self, file_path: str) -> np.ndarray:
        """
        加载音频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            音频数据
        """
        try:
            with wave.open(file_path, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                audio_bytes = wav_file.readframes(n_frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32767
                
                logger.info(f"音频已加载: {file_path} ({frame_rate}Hz, {n_channels}ch)")
                return audio_data
        except Exception as e:
            logger.error(f"加载音频失败: {e}")
            return np.array([])
    
    def get_buffer_data(self) -> np.ndarray:
        """获取缓冲区中的音频数据"""
        return np.array(list(self.audio_buffer), dtype=np.float32)
    
    def clear_buffer(self):
        """清空音频缓冲区"""
        self.audio_buffer.clear()
    
    def close(self):
        """关闭音频管理器"""
        if self.is_recording:
            self.stop_recording()
        if self.stream:
            self.stream.close()
        self.p.terminate()
        logger.info("音频管理器已关闭")
    
    def __del__(self):
        """析构函数"""
        try:
            self.close()
        except:
            pass
