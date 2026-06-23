"""
语音识别模块 - 使用 Wav2Vec2 端到端模型
支持中文语音识别、噪声处理、实时流式识别
"""

import os
import numpy as np
import librosa
import torch
import torchaudio
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from typing import Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """中文语音识别类"""
    
    # 预定义的命令集合（至少20个）
    COMMAND_KEYWORDS = {
        "开灯": ["开灯", "打开灯", "��亮起来"],
        "关灯": ["关灯", "关掉灯", "灯灭"],
        "打开浏览器": ["打开浏览器", "启动浏览器"],
        "关闭浏览器": ["关闭浏览器"],
        "打开计算器": ["打开计算器", "启动计算器"],
        "打开记事本": ["打开记事本", "启动记事本"],
        "截屏": ["截屏", "截图"],
        "打开文件管理器": ["打开文件管理器", "打开资源管理器"],
        "调高音量": ["调高音量", "增加音量"],
        "调低音量": ["调低音量", "降低音量"],
        "静音": ["静音", "关闭声音"],
        "打开音乐": ["打开音乐", "播放音乐"],
        "停止播放": ["停止播放", "暂停"],
        "下一首": ["下一首", "下一个"],
        "上一首": ["上一首", "上一个"],
        "打开视频": ["打开视频", "播放视频"],
        "全屏": ["全屏", "全屏显示"],
        "退出全屏": ["退出全屏", "退出"],
        "系统关机": ["系统关机", "关机", "电脑关机"],
        "系统重启": ["系统重启", "重启", "电脑重启"],
    }
    
    def __init__(self, config: Dict):
        """
        初始化语音识别器
        
        Args:
            config: 配置字典，包含 model_path, device, language等参数
        """
        self.config = config
        self.device = torch.device(config.get('device', 'cpu'))
        self.sample_rate = 16000  # Wav2Vec2 要求16kHz
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        
        logger.info(f"语音识别器初始化中... 使用设备: {self.device}")
        
        try:
            # 加载预训练模型和处理器
            model_path = config.get('model_path', 'jonatasgrosman/wav2vec2-large-xlsr-53-chinese')
            
            logger.info(f"加载处理器从: {model_path}")
            self.processor = Wav2Vec2Processor.from_pretrained(model_path)
            
            logger.info(f"加载模型从: {model_path}")
            self.model = Wav2Vec2ForCTC.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("语音识别模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def preprocess_audio(self, audio_data: np.ndarray, sr: int = None) -> np.ndarray:
        """
        预处理音频数据
        
        Args:
            audio_data: 音频数据 (numpy array)
            sr: 采样率
            
        Returns:
            预处理后的音频数据 (16kHz)
        """
        if sr is None:
            sr = self.sample_rate
        
        # 重采样到16kHz
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
        
        # 归一化
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        return audio_data
    
    def denoise_audio(self, audio_data: np.ndarray, noise_profile: np.ndarray = None) -> np.ndarray:
        """
        简单的噪声抑制处理
        
        Args:
            audio_data: 输入音频
            noise_profile: 噪声样本（可选）
            
        Returns:
            降噪后的音频
        """
        # 使用 librosa 的简单功能频谱减法
        S = np.abs(librosa.stft(audio_data))
        
        if noise_profile is not None:
            # 如果提供了噪声样本，用其谱来做减法
            noise_S = np.abs(librosa.stft(noise_profile))
            noise_mean = np.mean(noise_S, axis=1, keepdims=True)
            S = np.maximum(S - noise_mean, 0)
        else:
            # 简单的频谱减法（假设前100ms是噪声）
            noise_frames = int(0.1 * self.sample_rate / 512)
            noise_mean = np.mean(S[:, :noise_frames], axis=1, keepdims=True)
            S = np.maximum(S - 0.5 * noise_mean, 0)
        
        # 进行 iSTFT 恢复
        audio_denoised = librosa.istft(S)
        
        # 确保长度一致
        if len(audio_denoised) > len(audio_data):
            audio_denoised = audio_denoised[:len(audio_data)]
        elif len(audio_denoised) < len(audio_data):
            audio_denoised = np.pad(audio_denoised, (0, len(audio_data) - len(audio_denoised)))
        
        return audio_denoised
    
    def recognize(self, audio_data: np.ndarray, sr: int = None, 
                  denoise: bool = True) -> Tuple[str, float]:
        """
        识别音频文件
        
        Args:
            audio_data: 音频数据 (numpy array)
            sr: 采样率
            denoise: 是否进行降噪
            
        Returns:
            (识别文本, 置信度)
        """
        try:
            # 预处理音频
            audio_data = self.preprocess_audio(audio_data, sr)
            
            # 降噪
            if denoise:
                audio_data = self.denoise_audio(audio_data)
            
            # 使用处理器处理音频
            inputs = self.processor(audio_data, sampling_rate=self.sample_rate, 
                                   return_tensors="pt", padding=True)
            
            # 进行推理
            with torch.no_grad():
                logits = self.model(inputs.input_values.to(self.device)).logits
            
            # 获取预测的token ID
            predicted_ids = torch.argmax(logits, dim=-1)
            
            # 解码为文本
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # 计算置信度（基于logits的softmax最大值）
            probs = torch.softmax(logits, dim=-1)
            confidence = float(torch.max(probs))
            
            logger.info(f"识别结果: '{transcription}' (置信度: {confidence:.2%})")
            
            return transcription, confidence
        
        except Exception as e:
            logger.error(f"识别失败: {e}")
            return "", 0.0
    
    def recognize_command(self, audio_data: np.ndarray, sr: int = None) -> Tuple[str, str, float]:
        """
        识别并解析命令
        
        Args:
            audio_data: 音频数据
            sr: 采样率
            
        Returns:
            (命令名称, 识别文本, 置信度)
        """
        text, confidence = self.recognize(audio_data, sr)
        
        # 检查是否满足置信度阈值
        if confidence < self.confidence_threshold:
            logger.warning(f"置信度过低: {confidence:.2%} < {self.confidence_threshold:.2%}")
            return "", text, confidence
        
        # 尝试匹配命令
        best_command = ""
        best_score = 0.0
        
        for command, keywords in self.COMMAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    score = len(keyword) / len(text)  # 基于匹配长度的分数
                    if score > best_score:
                        best_command = command
                        best_score = score
        
        return best_command if best_command else "unknown", text, confidence
    
    def load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        加载音频文件
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            (音频数据, 采样率)
        """
        audio_data, sr = librosa.load(file_path, sr=None)
        return audio_data, sr
    
    def recognize_from_file(self, file_path: str, denoise: bool = True) -> Tuple[str, float]:
        """
        从文件识别语音
        
        Args:
            file_path: 音频文件路径
            denoise: 是否进行降噪
            
        Returns:
            (识别文本, 置信度)
        """
        audio_data, sr = self.load_audio_file(file_path)
        return self.recognize(audio_data, sr, denoise)
    
    def get_supported_commands(self) -> Dict[str, List[str]]:
        """获取支持的命令列表"""
        return self.COMMAND_KEYWORDS
    
    def add_custom_command(self, command_name: str, keywords: List[str]):
        """
        添加自定义命令
        
        Args:
            command_name: 命令名称
            keywords: 关键词列表
        """
        self.COMMAND_KEYWORDS[command_name] = keywords
        logger.info(f"添加自定义命令: {command_name}")
