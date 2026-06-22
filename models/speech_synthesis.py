"""
语音合成模块 - 使用高质量TTS生成自然流畅的中文语音
"""

import numpy as np
import threading
from typing import Optional
import io


class SpeechSynthesizer:
    """语音合成器"""
    
    def __init__(self, config: dict):
        """初始化语音合成器"""
        self.config = config
        self.engine = config.get('engine', 'edge-tts')
        self.voice = config.get('voice', 'zh-CN-XiaoxiuNeural')
        self.rate = config.get('rate', 1.0)
        self.volume = config.get('volume', 1.0)
        
        print(f"[*] 初始化语音合成引擎: {self.engine}")
        
        if self.engine == 'edge-tts':
            self._init_edge_tts()
        elif self.engine == 'pyttsx3':
            self._init_pyttsx3()
        else:
            print(f"[!] 未知的TTS引擎: {self.engine}")
    
    def _init_edge_tts(self):
        """初始化Edge TTS"""
        try:
            import edge_tts
            self.edge_tts = edge_tts
            print("[✓] Edge TTS初始化成功")
            self.synth_ready = True
        except ImportError:
            print("[!] Edge TTS未安装，使用备用方案")
            self.synth_ready = False
    
    def _init_pyttsx3(self):
        """初始化pyttsx3"""
        try:
            import pyttsx3
            self.engine_obj = pyttsx3.init()
            self.engine_obj.setProperty('rate', int(150 * self.rate))
            self.engine_obj.setProperty('volume', self.volume)
            print("[✓] pyttsx3初始化成功")
            self.synth_ready = True
        except ImportError:
            print("[!] pyttsx3未安装")
            self.synth_ready = False
    
    def synthesize(self, text: str) -> np.ndarray:
        """合成文本为语音"""
        if not text:
            return np.array([])
        
        try:
            if self.engine == 'edge-tts':
                return self._synthesize_edge_tts(text)
            elif self.engine == 'pyttsx3':
                return self._synthesize_pyttsx3(text)
            else:
                # 降级方案
                return self._synthesize_fallback(text)
        except Exception as e:
            print(f"[!] 语音合成失败: {e}")
            return np.array([])
    
    def _synthesize_edge_tts(self, text: str) -> np.ndarray:
        """使用Edge TTS合成"""
        try:
            import asyncio
            import io
            from pydub import AudioSegment
            
            async def get_audio():
                communicate = self.edge_tts.Communicate(text, self.voice)
                audio_bytes = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk['type'] == 'audio':
                        audio_bytes.write(chunk['data'])
                audio_bytes.seek(0)
                return audio_bytes
            
            # 运行异步获取音频
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(get_audio())
            loop.close()
            
            # 转换为numpy数组
            audio = AudioSegment.from_mp3(audio_bytes)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            
            # 归一化
            if len(samples) > 0:
                samples = samples / (2**15)
            
            return samples
            
        except Exception as e:
            print(f"[!] Edge TTS合成失败: {e}")
            return np.array([])
    
    def _synthesize_pyttsx3(self, text: str) -> np.ndarray:
        """使用pyttsx3合成"""
        try:
            output_path = "/tmp/tts_output.wav"
            self.engine_obj.save_to_file(text, output_path)
            self.engine_obj.runAndWait()
            
            import scipy.io.wavfile as wavfile
            sample_rate, audio_data = wavfile.read(output_path)
            
            # 转换为float32
            audio_data = audio_data.astype(np.float32)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            return audio_data / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else audio_data
            
        except Exception as e:
            print(f"[!] pyttsx3合成失败: {e}")
            return np.array([])
    
    def _synthesize_fallback(self, text: str) -> np.ndarray:
        """降级方案 - 使用简单的文字转语音提示"""
        print(f"[*] 回复: {text}")
        # 生成简单的音调序列作为反馈
        duration = len(text) * 0.1  # 基于文字长度
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # 生成简单的音调
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4音
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
        
        return audio
    
    def batch_synthesize(self, texts: list) -> list:
        """批量合成多个文本"""
        results = []
        for text in texts:
            audio = self.synthesize(text)
            results.append(audio)
        return results
