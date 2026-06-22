# 安装指南

## 系统要求

- Python 3.8 或更高版本
- pip 包管理器
- Android SDK（ADB命令行工具）
- 麦克风和扬声器
- 至少 4GB RAM

## 步骤 1: 安装Python依赖

```bash
pip install -r requirements.txt
```

如果某些包安装失败，可以逐个安装：

```bash
pip install torch torchaudio transformers librosa
pip install PyQt5 pyaudio
pip install pyttsx3 edge-tts
pip install pyyaml
```

## 步骤 2: 安装 ADB（Android Debug Bridge）

### Windows
1. 下载 Android SDK Platform Tools: https://developer.android.com/tools/releases/platform-tools
2. 解压到任意目录（如 `C:\adb`）
3. 将该目录添加到系统 PATH 环境变量
4. 打开命令提示符，运行 `adb version` 验证安装

### macOS
```bash
brew install android-platform-tools
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install adb
```

## 步骤 3: 连接 Android 设备

### USB连接
1. 在 Android 设备上启用「开发者选项」：
   - 设置 → 关于手机 → 连续点击"版本号"7次
2. 在「开发者选项」中启用「USB 调试」
3. 用USB线连接设备到电脑
4. 在设备上同意USB调试权限
5. 验证连接：
```bash
adb devices
```

### WiFi连接（可选）
1. 确保设备和电脑在同一WiFi网络
2. 在设备上开启"无线调试"
3. 获取配对码和IP地址
4. 配对设备：
```bash
adb pair 192.168.x.x:port
```
5. 连接设备：
```bash
adb connect 192.168.x.x:5555
```

## 步骤 4: 下载预训练模型

首次运行时，系统会自动下载预训练模型。确保网络连接正常。

预训练模型包括：
- Wav2Vec2 中文语音识别模型 (~2GB)
- 语音合成模型

## 步骤 5: 启动系统

### 方式 1: 同一台机器上运行

```bash
# 终端1：启动服务器
python run_server.py

# 终端2：启动客户端
python main.py
```

### 方式 2: 不同机器上运行

**服务器端（连接ADB设备的机器）：**
```bash
python run_server.py
```

**客户端端（任意机器）：**
1. 编辑 `config.yaml`，修改服务器地址：
```yaml
server:
  host: "192.168.x.x"  # 服务器IP地址
  port: 5000
```

2. 启动客户端：
```bash
python main.py
```

## 故障排除

### 问题 1: "adb: command not found"
- 检查 ADB 是否已正确安装
- 检查 PATH 环境变量是否包含 ADB 路径
- 重启命令行或IDE

### 问题 2: "No devices found"
- 检查 USB 连接是否正常
- 确保在设备上授予USB调试权限
- 运行 `adb kill-server && adb start-server` 重启ADB

### 问题 3: 模型加载失败
- 检查网络连接（下载预训练模型需要）
- 确保有足够的磁盘空间（至少 5GB）
- 尝试手动下载模型：https://huggingface.co

### 问题 4: 语音识别不工作
- 检查麦克风是否正确连接和配置
- 检查音量设置
- 在 `config.yaml` 中修改音频设备索引

### 问题 5: 连接服务器失败
- 检查服务器是否正在运行
- 检查防火墙设置，确保允许 5000 端口通信
- 检查网络连接，确保客户端和服务器在同一网络中

## 下一步

查看 README.md 了解系统使用方法。
