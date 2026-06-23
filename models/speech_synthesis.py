"""
语音合成模块 - 使用多种TTS引擎
支持多种声音、语速、音量调整、情感表达
"""

import os
import asyncio
import numpy as np
import torch
import torchaudio
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SpeechSynthesizer:
    """语音合成类"""
    
    # 支持的引擎
    SUPPORTED_ENGINES = {
        'edge-tts': 'Edge TTS (微软在线)',
        'pyttsx3': 'PyTTSX3 (本地引擎)',
        'glow-tts': 'Glow-TTS (高质量端到端)',
    }
    
    # Edge TTS 中文声音选项
    EDGE_TTS_VOICES = {
        'xiaoxiao': 'zh-CN-XiaoxiuNeural',      # 小小，女性，高音
        'xiaoxuan': 'zh-CN-XiaoxuanNeural',     # 小萱，女性，甜美
        'xiaoyi': 'zh-CN-XiaoyiNeural',         # 小艺，女性，标准
        'yunxi': 'zh-CN-YunxiNeural',           # 云希，男性，标准
        'yunyang': 'zh-CN-YunyangNeural',       # 云阳，男性，低沉
    }
    
    def __init__(self, config: Dict):
        """
        初始化语音合成器
        
        Args:
            config: 配置字典，包含 engine, voice, rate, volume 等参数
        """
        self.config = config
        self.engine = config.get('engine', 'edge-tts')
        self.voice = config.get('voice', 'zh-CN-XiaoxiuNeural')
        self.rate = config.get('rate', 1.0)
        self.volume = config.get('volume', 1.0)
        
        logger.info(f"语音合成器初始化: 引擎={self.engine}, 声音={self.voice}")
        
        # 初始化不同的TTS引擎
        self._init_engine()
    
    def _init_engine(self):
        """初始化TTS引擎"""
        try:
            if self.engine == 'edge-tts':
                try:
                    import edge_tts
                    logger.info("Edge TTS 初始化成功")
                except ImportError:
                    logger.error("edge-tts 未安装，请运行: pip install edge-tts")
                    raise
            
            elif self.engine == 'pyttsx3':
                try:
                    import pyttsx3
                    self.tts_engine = pyttsx3.init()
                    logger.info("PyTTSX3 初始化成功")
                except ImportError:
                    logger.error("pyttsx3 未安装，请运行: pip install pyttsx3")
                    raise
            
            elif self.engine == 'glow-tts':
                logger.info("Glow-TTS 引擎（需要手动配置模型路径）")
        
        except Exception as e:
            logger.error(f"TTS引擎初始化失败: {e}")
            raise
    
    async def synthesize_edge_tts(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        使用 Edge TTS 合成语音
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径（可选）
            
        Returns:
            音频数据 (bytes) 或保存到文件
        """
        try:
            import edge_tts
            
            # 构建语速参数
            rate = f"{(self.rate - 1) * 100:+.0f}%"  # 转换为百分比
            
            # 创建合成器
            communicate = edge_tts.Communicate(text, self.voice, rate=rate)
            
            audio_data = b''
            
            # 接收音频数据
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    audio_data += chunk['data']
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"音频已保存到: {output_path}")
            
            return audio_data
        
        except Exception as e:
            logger.error(f"Edge TTS 合成失败: {e}")
            return b''
    
    def synthesize_pyttsx3(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        使用 PyTTSX3 合成语音
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            
        Returns:
            音频数据
        """
        try:
            import pyttsx3
            
            if output_path is None:
                output_path = 'temp_output.wav'
            
            # 配置引擎
            self.tts_engine.setProperty('rate', 150 * self.rate)
            self.tts_engine.setProperty('volume', self.volume)
            
            # 合成并保存
            self.tts_engine.save_to_file(text, output_path)
            self.tts_engine.runAndWait()
            
            # 读取音频数据
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            logger.info(f"PyTTSX3 合成完成: {output_path}")
            return audio_data
        
        except Exception as e:
            logger.error(f"PyTTSX3 合成失败: {e}")
            return b''
    
    async def synthesize(self, text: str, output_path: Optional[str] = None, 
                        emotion: str = 'neutral') -> bytes:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径（可选）
            emotion: 情感类型 ('neutral', 'cheerful', 'serious', 'angry', 'sad')
            
        Returns:
            音频数据
        """
        if not text:
            logger.warning("文本为空，跳过合成")
            return b''
        
        try:
            # 根据情感调整语音参数
            original_rate = self.rate
            original_volume = self.volume
            
            if emotion == 'cheerful':
                self.rate = min(1.3, self.rate * 1.2)
                self.volume = min(1.0, self.volume * 1.1)
            elif emotion == 'serious':
                self.rate = max(0.8, self.rate * 0.9)
            elif emotion == 'angry':
                self.rate = min(1.5, self.rate * 1.3)
                self.volume = min(1.0, self.volume * 1.2)
            elif emotion == 'sad':
                self.rate = max(0.7, self.rate * 0.8)
                self.volume = max(0.5, self.volume * 0.8)
            
            logger.info(f"合成语音: '{text}' (情感: {emotion})")
            
            if self.engine == 'edge-tts':
                audio_data = await self.synthesize_edge_tts(text, output_path)
            elif self.engine == 'pyttsx3':
                audio_data = self.synthesize_pyttsx3(text, output_path)
            else:
                logger.error(f"不支持的引擎: {self.engine}")
                audio_data = b''
            
            # 恢复原始参数
            self.rate = original_rate
            self.volume = original_volume
            
            return audio_data
        
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return b''
    
    def synthesize_sync(self, text: str, output_path: Optional[str] = None,
                        emotion: str = 'neutral') -> bytes:
        """
        同步合成语音（兼容异步调用）
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            emotion: 情感类型
            
        Returns:
            音频数据
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.synthesize(text, output_path, emotion))
    
    def adjust_pitch(self, audio_data: np.ndarray, pitch_shift: int) -> np.ndarray:
        """
        调整音调
        
        Args:
            audio_data: 输入音频
            pitch_shift: 音调移位（半音数）
            
        Returns:
            调整后的音频
        """
        import librosa
        
        S = np.abs(librosa.stft(audio_data))
        phase = np.angle(librosa.stft(audio_data))
        
        # 使用 librosa 的音调转换
        shifted = librosa.phase_vocoder(S, 1.0)
        
        return librosa.istft(shifted * np.exp(1.j * phase))
    
    def adjust_speed(self, audio_data: np.ndarray, speed_factor: float) -> np.ndarray:
        """
        调整语速
        
        Args:
            audio_data: 输入音频
            speed_factor: 语速因子（1.0为正常）
            
        Returns:
            调整后的音频
        """
        import librosa
        
        return librosa.effects.time_stretch(audio_data, rate=speed_factor)
    
    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的声音列表"""
        if self.engine == 'edge-tts':
            return self.EDGE_TTS_VOICES
        else:
            return {}
    
    def set_voice(self, voice_name: str):
        """
        设置语音
        
        Args:
            voice_name: 声音名称
        """
        if self.engine == 'edge-tts':
            if voice_name in self.EDGE_TTS_VOICES:
                self.voice = self.EDGE_TTS_VOICES[voice_name]
                logger.info(f"设置声音: {voice_name}")
            else:
                logger.warning(f"未知的声音: {voice_name}")
        else:
            logger.warning(f"引擎 {self.engine} 不支持声音选择")
    
    def test_synthesis(self, text: str = "你好，这是一个语音合成测试。") -> bytes:
        """
        测试语音合成
        
        Args:
            text: 测试文本
            
        Returns:
            音频数据
        """
        logger.info("开始语音合成测试...")
        return self.synthesize_sync(text)
