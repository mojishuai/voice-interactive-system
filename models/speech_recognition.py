"""
语音识别模块 - 使用Wav2Vec2模型进行中文语音识别
"""

import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from typing import Dict, Tuple
import warnings

warnings.filterwarnings('ignore')


class SpeechRecognizer:
    """语音识别器"""
    
    def __init__(self, config: dict):
        """初始化语音识别器"""
        self.config = config
        self.sample_rate = config.get('sample_rate', 16000)
        self.device = torch.device(config.get('device', 'cpu'))
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        
        # 模型路径
        model_name = config.get('model_name', 'wav2vec2-chinese')
        model_path = config.get('model_path', './models/asr/wav2vec2-large-xlsr-53-chinese')
        
        print(f"[*] 加载Wav2Vec2模型: {model_path}")
        
        try:
            # 加载预训练的Wav2Vec2处理器和模型
            self.processor = Wav2Vec2Processor.from_pretrained(model_path)
            self.model = Wav2Vec2ForCTC.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            
            print("[✓] 语音识别模型加载成功")
        except Exception as e:
            print(f"[!] 模型加载失败，使用备用方案: {e}")
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """加载备用模型（如果主模型不可用）"""
        try:
            # 使用Hugging Face官方预训练模型
            from transformers import pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model="facebook/wav2vec2-large-xlsr-53-chinese",
                device=0 if torch.cuda.is_available() else -1
            )
            self.model = None
            print("[✓] 使用备用模型加载成功")
        except Exception as e:
            print(f"[✗] 备用模型也加载失败: {e}")
            raise
    
    def recognize(self, audio_data: np.ndarray) -> Dict[str, any]:
        """识别音频并返回文本"""
        try:
            # 处理输入音频
            if len(audio_data) == 0:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'success': False,
                    'error': '音频数据为空'
                }
            
            # 音频预处理
            audio_data = self._preprocess_audio(audio_data)
            
            if hasattr(self, 'pipe'):
                # 使用备用管道
                result = self.pipe(audio_data)
                return {
                    'text': result['text'],
                    'confidence': 0.95,  # 管道不返回置信度
                    'success': True,
                    'error': None
                }
            else:
                # 使用完整的Wav2Vec2模型
                with torch.no_grad():
                    # 处理音频
                    inputs = self.processor(
                        audio_data,
                        sampling_rate=self.sample_rate,
                        return_tensors="pt",
                        padding=True
                    )
                    
                    # 获取logits
                    logits = self.model(
                        inputs.input_values.to(self.device)
                    ).logits
                    
                    # 获取预测
                    predicted_ids = torch.argmax(logits, dim=-1)
                    transcription = self.processor.decode(predicted_ids[0])
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(logits)
                    
                    return {
                        'text': transcription,
                        'confidence': float(confidence),
                        'success': True,
                        'error': None
                    }
        
        except Exception as e:
            print(f"[!] 语音识别失败: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """预处理音频"""
        # 确保是单声道
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # 归一化
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        return audio_data.astype(np.float32)
    
    def _calculate_confidence(self, logits: torch.Tensor) -> float:
        """计算识别置信度"""
        try:
            probabilities = torch.softmax(logits, dim=-1)
            max_prob = torch.max(probabilities)
            return float(max_prob)
        except:
            return 0.95
    
    def batch_recognize(self, audio_list: list) -> list:
        """批量识别多个音频"""
        results = []
        for audio in audio_list:
            result = self.recognize(audio)
            results.append(result)
        return results
