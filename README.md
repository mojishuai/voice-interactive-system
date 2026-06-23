# 语音人机交互系统 - 演示脚本

首先，请确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

## 快速开始

### 方法1：在同一台机器上运行（推荐用于测试）

**终端1 - 启动服务器：**
```bash
python run_server.py
```

**终端2 - 启动客户端：**
```bash
python main.py
```

### 方法2：在不同机器上运行

**服务器端：**
```bash
python run_server.py
```

**客户端端：**
编辑 `config.yaml`，修改服务器地址：
```yaml
server:
  host: "192.168.x.x"  # 服��器IP
  port: 5000
```

然后运行：
```bash
python main.py
```

## 系统功能

### 核心功能
- ✅ **语音识别**：使用Wav2Vec2模型识别20+中文命令
- ✅ **语音合成**：使用Edge TTS生成自然流畅的语音
- ✅ **命令解析**：自动识别并解析语音命令
- ✅ **设备控制**：支持PC和Android设备控制
- ✅ **实时反馈**：通过GUI显示识别和执行结果

### 支持的命令（20+）

#### 照明控制
- 开灯 / 关灯

#### 应用程序
- 打开浏览器 / 关闭浏览器
- 打开计算器 / 打开记事本
- 打开文件管理器

#### 系统控制
- 截屏
- 调高音量 / 调低音量 / 静音
- 系统关机 / 系统重启

#### 媒体控制
- 打开音乐 / 打开视频
- 停止播放 / 下一首 / 上一首
- 全屏 / 退出全屏

### GUI界面说明

1. **开始录音按钮**：点击开始录音，再次点击停止并处理
2. **事件日志**：实时显示系统运行过程
3. **进度条**：显示语音处理进度
4. **测试合成**：测试语音合成功能

## 配置说明

### config.yaml 重要参数

```yaml
# 服务器配置
server:
  host: "127.0.0.1"     # 监听地址
  port: 5000             # 监听端口

# 音频配置
audio:
  sample_rate: 16000     # 采样率
  channels: 1            # 单声道
  device_index: -1       # -1为默认设备

# 语音识别配置
asr:
  device: "cuda"         # 使用GPU加速 (cuda/cpu)
  confidence_threshold: 0.5  # 置信度阈值

# 语音合成配置  
tts:
  engine: "edge-tts"     # TTS引擎
  voice: "zh-CN-XiaoxiuNeural"  # 女性声音
  rate: 1.0              # 语速（0.5-2.0）
```

## 故障排除

### 问题1："ModuleNotFoundError: No module named 'transformers'"
**解决方案**：
```bash
pip install -r requirements.txt
```

### 问题2："CUDA out of memory"
**解决方案**：在config.yaml中设置CPU模式：
```yaml
asr:
  device: "cpu"
```

### 问题3："Failed to connect to server"
**解决方案**：
- 确保服务器已启动
- 检查防火墙是否允许5000端口
- 检查网络连接

### 问题4："No module named 'pyaudio'"
**解决方案**：
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio
```

## 模型信息

### 语音识别模型
- **模型**：Wav2Vec2-Large-XLSR-53-Chinese
- **来源**：Hugging Face
- **大小**：~2GB
- **支持语言**：中文
- **自动下载**：首次运行时自动下载

### 语音合成
- **主要引擎**：Microsoft Edge TTS（在线）
- **备选方案**：PyTTSX3（本地）
- **支持声音**：多种中文女性/男性声音

## 扩展功能

### 添加自定义命令

在 `models/speech_recognition.py` 中修改 `COMMAND_KEYWORDS`：

```python
COMMAND_KEYWORDS = {
    "您的命令": ["关键词1", "关键词2"],
    # ...
}
```

### 添加新设备

在 `server/device_controller.py` 中创建新的设备控制类：

```python
class MyDeviceController(DeviceController):
    def execute_command(self, command: str) -> bool:
        # 实现您的命令逻辑
        pass
```

## 系统架构

```
客户端 (main.py)
├── GUI (PyQt5)
├── 音频管理 (pyaudio)
├── 语音识别 (Wav2Vec2)
├── 语音合成 (Edge TTS)
└── 网络通信 (Socket)
        ↓
    服务器 (run_server.py)
    ├── 命令接收
    ├── 设备管理
    ├── PC控制 (subprocess)
    └── Android控制 (ADB)
```

## 许可证

MIT License

## 作者

@mojishuai
