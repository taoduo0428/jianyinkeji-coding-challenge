"""
TikTok 下载器配置文件
"""
import os

# ==================== 基础配置 ====================

# TikTok 用户名（要爬取的账号）
TARGET_USERNAME = "nba"

# 下载视频数量
MAX_VIDEOS = 20

# 输出目录（相对于Scrapy文件夹）
OUTPUT_DIR = "../data"

# 子文件夹配置
METADATA_SUBDIR = "元数据"      # 存放视频文件和元数据JSON
TRANSCRIPTION_SUBDIR = "转录数据"  # 存放转录后的文本文件

# ==================== TikTok API 配置 ====================

# ms_token（从浏览器Cookie中获取，可选）
# 获取方式：访问 tiktok.com -> F12 -> Application -> Cookies -> ms_token
# 已从浏览器Cookie中提取（2025-03-08更新）
MS_TOKEN = os.environ.get("ms_token", "MdRmfSNzO0JY_s7_pDL021qF92l8U24esdGp2toOILJ4y5T9EldHrk2D81qP2HllGkY5Qnn6gGMSikVqWfm2XikfDAPvcG_MPiConeJvY_pjnErszK73F6e6G76VeDPikYLGiOTgNtnsnVKrm6Cth0-Qers=")

# 浏览器设置
BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
HEADLESS_MODE = False      # True=无界面模式, False=显示浏览器

# 会话配置
NUM_SESSIONS = 1           # 并发会话数
SLEEP_AFTER = 3            # 创建会话后等待时间（秒）
SLEEP_BETWEEN_VIDEOS = 2   # 每个视频下载之间的等待时间（秒）

# ==================== 数据处理配置 ====================

# 是否清理元数据（移除字幕信息以减小文件大小）
CLEAN_METADATA = True

# 是否生成Excel汇总
GENERATE_EXCEL = True

# Excel文件名
EXCEL_FILENAME = "视频汇总.xlsx"

# ==================== 文件命名配置 ====================

# 视频文件命名格式
VIDEO_FILENAME_FORMAT = "{video_id}.mp4"

# 元数据文件命名格式
METADATA_FILENAME_FORMAT = "{video_id}_metadata.json"

# 清理后的元数据文件命名格式
CLEANED_METADATA_FILENAME_FORMAT = "{video_id}_metadata_cleaned.json"

# ==================== Excel 列配置 ====================

# Excel中包含的列（按顺序）
EXCEL_COLUMNS = [
    '视频ID', '视频URL', '描述', '发布时间',
    '点赞数', '评论数', '分享数', '播放数', '收藏数',
    '作者ID', '作者昵称', '作者粉丝数',
    '视频时长(秒)', '视频宽度', '视频高度', '视频比例',
    '话题标签', '话题数量', '字幕语言数', '字幕总数',
    '音乐标题', '音乐作者',
    '本地视频文件', '视频文件大小(MB)'
]

# ==================== 调试配置 ====================

# 是否显示详细日志
VERBOSE = True

# 是否在下载失败时继续
CONTINUE_ON_ERROR = True

# 失败重试配置
MAX_RETRIES = 3            # 最大重试次数
RETRY_DELAY = 5            # 重试前等待时间（秒）
