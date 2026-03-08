# TikTok 视频下载与转录工具

一个完整的 TikTok 视频数据采集和处理流程：从视频下载、元数据提取、到语音转文字，一站式解决方案。

## 🎯 核心功能

**视频下载** → **元数据提取** → **语音转录** → **数据汇总**

- 下载指定用户的 TikTok 视频（MP4）
- 提取完整元数据（点赞、播放、评论、作者信息等）
- 使用 AI 模型转录视频语音为文字
- 自动生成 Excel 数据汇总表

## 🛠️ 技术栈

| 组件     | 技术                            | 用途                 |
| -------- | ------------------------------- | -------------------- |
| 视频下载 | TikTokApi + Playwright          | 自动化浏览器抓取视频 |
| 语音转录 | faster-whisper (OpenAI Whisper) | AI 语音识别          |
| 数据处理 | pandas + openpyxl               | Excel 数据分析       |
| 运行环境 | Python 3.8+                     | -                    |

## 📁 项目结构

```
Scrapy/
├── tiktok_downloader.py       # 视频下载器
├── config.py                  # 下载配置
├── video_transcriber.py       # 语音转录器
└── transcription_config.py    # 转录配置

data/
├── 元数据/                    # 视频 + 元数据JSON
├── 转录数据/                  # 转录文本
└── 视频汇总.xlsx              # Excel汇总
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 视频下载依赖
pip install TikTokApi pandas openpyxl
python -m playwright install chromium

# 语音转录依赖（可选）
pip install faster-whisper
```

### 2. 配置目标

编辑 `config.py`：

```python
TARGET_USERNAME = "nba"      # TikTok 用户名
MAX_VIDEOS = 20              # 下载数量
OUTPUT_DIR = "../data"       # 输出目录
```

### 3. 运行完整流程

```bash
# 步骤1: 下载视频和元数据
python tiktok_downloader.py

# 步骤2: 转录视频为文字
python video_transcriber.py

# 步骤3: 查看结果
# - 视频和元数据: data/元数据/
# - 转录文本: data/转录数据/
# - Excel汇总: data/视频汇总.xlsx
```

## 📊 输出数据

### 文件结构

```
data/
├── 元数据/
│   ├── {video_id}.mp4                      # 视频文件
│   ├── {video_id}_metadata.json            # 完整元数据（70-100KB）
│   └── {video_id}_metadata_cleaned.json    # 精简元数据（20-35KB，减少66%）
├── 转录数据/
│   └── {video_id}_transcript.txt           # 转录文本（带时间戳）
└── 视频汇总.xlsx                            # Excel汇总表
```

### Excel 数据列（24列）

**视频信息**: 视频ID、URL、描述、发布时间、时长、分辨率
**互动数据**: 点赞数、评论数、分享数、播放数、收藏数
**作者信息**: 作者ID、昵称、粉丝数
**内容标签**: 话题标签、话题数量、字幕语言数
**音乐信息**: 音乐标题、音乐作者
**文件信息**: 本地文件路径、文件大小

## ⚙️ 核心配置

### 下载器配置 (config.py)

```python
TARGET_USERNAME = "nba"        # 目标用户
MAX_VIDEOS = 20                # 下载数量
OUTPUT_DIR = "../data"         # 输出目录
MS_TOKEN = "..."               # TikTok token（可选，提高成功率）
CLEAN_METADATA = True          # 清理元数据（减小66%文件大小）
GENERATE_EXCEL = True          # 生成Excel汇总
```

### 转录器配置 (transcription_config.py)

```python
MODEL_SIZE = "base"            # 模型: tiny/base/small/medium/large-v2
DEVICE = "cpu"                 # 设备: cpu/cuda（GPU加速）
LANGUAGE = None                # 语言: None（自动检测）/zh/en
OUTPUT_FORMAT = "txt"          # 格式: txt/srt/vtt/json
INCLUDE_TIMESTAMPS = True      # 是否包含时间戳
```

## 🔧 高级功能

### 提高下载成功率

获取 `ms_token` 并设置环境变量：

1. 浏览器访问 https://www.tiktok.com
2. F12 → Application → Cookies → 复制 `ms_token`
3. 设置环境变量：

```bash
# Windows
set ms_token=你的token值

# Linux/Mac
export ms_token="你的token值"
```

### 转录模型选择

| 模型     | 速度 | 精度 | 内存  | 适用场景         |
| -------- | ---- | ---- | ----- | ---------------- |
| tiny     | 最快 | 较低 | ~1GB  | 快速测试         |
| base     | 快   | 一般 | ~1GB  | 日常使用（推荐） |
| small    | 中等 | 较好 | ~2GB  | 平衡选择         |
| medium   | 慢   | 好   | ~5GB  | 高质量需求       |
| large-v2 | 最慢 | 最好 | ~10GB | 专业级转录       |

### GPU 加速

如果有 NVIDIA 显卡：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

修改 `transcription_config.py`：

```python
DEVICE = "cuda"
COMPUTE_TYPE = "float16"
```

## 📝 数据说明

### 元数据清理

**完整元数据** (`*_metadata.json`, 70-100KB)
包含所有原始数据，包括50+种语言的字幕URL（占70-80%空间）

**精简元数据** (`*_metadata_cleaned.json`, 20-35KB)
移除字幕详细数据，保留统计信息，减少66%文件大小

### 转录文本格式

**TXT 格式（带时间戳）：**

```
[0.00s -> 2.60s] Like this in 10 to the early,
[2.60s -> 4.40s] Yo-Kit stopped at the flexion out of bounds.
```

**SRT 格式（字幕文件）：**

```
1
00:00:00,000 --> 00:00:02,600
Like this in 10 to the early,
```

## 📌 注意事项

- 遵守 TikTok 服务条款，仅用于个人学习和研究
- 尊重内容创作者的版权
- 转录功能建议至少 4GB RAM
- GPU 加速需要 NVIDIA 显卡和 CUDA 支持
