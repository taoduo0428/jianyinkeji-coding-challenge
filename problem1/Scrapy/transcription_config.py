"""
视频转录配置文件
"""
import os

# ==================== 路径配置 ====================

# 输入目录（视频所在位置，相对于Scrapy文件夹）
INPUT_DIR = os.path.join("..", "data", "元数据")

# 输出目录（转录结果保存位置，相对于Scrapy文件夹）
OUTPUT_DIR = os.path.join("..", "data", "转录数据")

# ==================== Whisper 模型配置 ====================

# 模型大小选择
# 可选: "tiny", "base", "small", "medium", "large", "large-v2", "large-v3"
# tiny: 最快，精度最低
# base: 较快，精度一般（推荐用于测试）
# small: 平衡
# medium: 较慢，精度较高
# large-v2: 最慢，精度最高（推荐用于正式使用）
MODEL_SIZE = "base"

# 设备选择
# "cpu": 使用CPU（所有平台都支持）
# "cuda": 使用NVIDIA GPU（需要CUDA支持）
# "auto": 自动选择（有GPU用GPU，没有用CPU）
DEVICE = "cpu"

# 计算类型
# CPU: "int8", "int16", "float32"
# GPU: "float16", "int8_float16", "int8"
COMPUTE_TYPE = "int8"

# ==================== 转录配置 ====================

# 语言设置
# None: 自动检测
# "zh": 中文
# "en": 英文
# "ja": 日语
# "ko": 韩语
LANGUAGE = None  # 自动检测

# 初始提示词（帮助模型更好地识别）
# 中文视频建议: "以下是简体中文普通话:"
# 英文视频建议: None 或 "The following is in English:"
INITIAL_PROMPT = None

# Beam size（影响精度和速度）
# 1-5: 较快，精度较低
# 5: 平衡（推荐）
# 10+: 较慢，精度较高
BEAM_SIZE = 5

# ==================== 输出格式配置 ====================

# 转录文件格式
# 支持的格式: "txt", "srt", "vtt", "json"
OUTPUT_FORMAT = "txt"

# 是否包含时间戳
INCLUDE_TIMESTAMPS = True

# 时间戳格式
# "seconds": [0.00s -> 3.50s]
# "time": [00:00:00 -> 00:00:03]
TIMESTAMP_FORMAT = "seconds"

# ==================== 处理配置 ====================

# 支持的视频格式
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

# 是否跳过已存在的转录文件
SKIP_EXISTING = True

# 是否显示详细日志
VERBOSE = True

# 进度输出频率（每处理多少个片段输出一次进度）
PROGRESS_FREQUENCY = 50

# 进度输出时间间隔（秒）
PROGRESS_INTERVAL = 10

# ==================== 批处理配置 ====================

# 是否批量处理所有视频
BATCH_MODE = True

# 最大处理视频数量（None表示处理所有）
MAX_VIDEOS = None

# 是否在出错时继续处理下一个视频
CONTINUE_ON_ERROR = True
