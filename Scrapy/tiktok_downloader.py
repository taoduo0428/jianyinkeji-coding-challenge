"""
TikTok 视频下载器 
1. 下载指定用户的视频和元数据
2. 自动清理元数据（移除字幕数据）
3. 生成Excel汇总表
4. 创建子文件夹分类存储数据
"""
from TikTokApi import TikTokApi
import asyncio
import os
import json
from datetime import datetime
import pandas as pd
from config import *


class TikTokDownloader:
    """TikTok视频下载器类"""
    
    def __init__(self, username=TARGET_USERNAME, max_videos=MAX_VIDEOS, output_dir=OUTPUT_DIR):
        """
        初始化下载器
        
        参数:
            username: TikTok用户名
            max_videos: 下载视频数量
            output_dir: 输出目录
        """
        self.username = username
        self.max_videos = max_videos
        self.output_dir = output_dir
        
        # 子文件夹路径
        self.metadata_dir = None
        self.transcription_dir = None
        
        self.all_videos_info = []
        self.success_count = 0
        self.fail_count = 0
        
    def setup_output_dir(self):
        """创建输出目录和子文件夹"""
        # 确保输出目录是绝对路径或相对于脚本所在目录
        if not os.path.isabs(self.output_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.normpath(os.path.join(script_dir, self.output_dir))
        
        # 创建主目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            if VERBOSE:
                print(f"✓ 创建主目录: {self.output_dir}")
        else:
            if VERBOSE:
                print(f"✓ 使用主目录: {self.output_dir}")
        
        # 创建子文件夹
        self.metadata_dir = os.path.join(self.output_dir, METADATA_SUBDIR)
        self.transcription_dir = os.path.join(self.output_dir, TRANSCRIPTION_SUBDIR)
        
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir)
            if VERBOSE:
                print(f"✓ 创建子文件夹: {METADATA_SUBDIR}/")
        
        if not os.path.exists(self.transcription_dir):
            os.makedirs(self.transcription_dir)
            if VERBOSE:
                print(f"✓ 创建子文件夹: {TRANSCRIPTION_SUBDIR}/")
        
        print()  # 空行
    
    @staticmethod
    def clean_metadata(data):
        """
        清理元数据，移除字幕信息以减小文件大小
        
        参数:
            data: 原始视频数据字典
            
        返回:
            清理后的数据字典
        """
        if not CLEAN_METADATA:
            return data
            
        cleaned = data.copy()
        
        # 移除字幕数据
        if 'video' in cleaned and 'subtitleInfos' in cleaned['video']:
            subtitle_count = len(cleaned['video']['subtitleInfos'])
            cleaned['video']['subtitleInfos'] = f"[已移除 {subtitle_count} 个字幕数据以减小文件大小]"
        
        return cleaned
    
    @staticmethod
    def extract_video_info(video_data):
        """
        从视频数据中提取关键信息用于Excel
        
        参数:
            video_data: 视频数据字典
            
        返回:
            提取的信息字典
        """
        info = {}
        
        # 基本信息
        info['视频ID'] = video_data.get('id', '')
        info['描述'] = video_data.get('desc', '')
        
        # 时间信息
        create_time = video_data.get('createTime', '')
        if create_time:
            try:
                timestamp = int(create_time)
                info['发布时间'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                info['发布时间'] = create_time
        else:
            info['发布时间'] = ''
        
        # 统计数据
        stats = video_data.get('stats') or video_data.get('statsV2') or {}
        info['点赞数'] = stats.get('diggCount', 0)
        info['评论数'] = stats.get('commentCount', 0)
        info['分享数'] = stats.get('shareCount', 0)
        info['播放数'] = stats.get('playCount', 0)
        info['收藏数'] = stats.get('collectCount', 0)
        
        # 作者信息
        author = video_data.get('author', {})
        info['作者ID'] = author.get('uniqueId', '')
        info['作者昵称'] = author.get('nickname', '')
        info['作者粉丝数'] = video_data.get('authorStats', {}).get('followerCount', 0)
        
        # 视频信息
        video = video_data.get('video', {})
        info['视频时长(秒)'] = video.get('duration', 0)
        info['视频宽度'] = video.get('width', 0)
        info['视频高度'] = video.get('height', 0)
        info['视频比例'] = video.get('ratio', '')
        
        # 字幕信息
        subtitle_infos = video.get('subtitleInfos', [])
        if isinstance(subtitle_infos, list):
            info['字幕语言数'] = len(set([s.get('LanguageCodeName', '') for s in subtitle_infos]))
            info['字幕总数'] = len(subtitle_infos)
        else:
            info['字幕语言数'] = 0
            info['字幕总数'] = 0
        
        # 话题标签
        challenges = video_data.get('challenges', [])
        hashtags = [c.get('title', '') for c in challenges if c.get('title')]
        info['话题标签'] = ', '.join(hashtags) if hashtags else ''
        info['话题数量'] = len(hashtags)
        
        # 音乐信息
        music = video_data.get('music', {})
        info['音乐标题'] = music.get('title', '')
        info['音乐作者'] = music.get('authorName', '')
        
        # 视频URL
        video_id = info['视频ID']
        author_id = info['作者ID']
        if video_id and author_id:
            info['视频URL'] = f"https://www.tiktok.com/@{author_id}/video/{video_id}"
        else:
            info['视频URL'] = ''
        
        return info
    
    async def collect_video_list(self, api):
        """
        收集视频列表
        
        参数:
            api: TikTokApi实例
            
        返回:
            视频信息列表
        """
        print(f"正在获取 @{self.username} 的视频列表...")
        user = api.user(username=self.username)
        
        video_list = []
        async for video in user.videos(count=self.max_videos):
            # 手动限制数量
            if len(video_list) >= self.max_videos:
                break
                
            video_id = video.id
            username = video.author.username if hasattr(video.author, 'username') else self.username
            url = f"https://www.tiktok.com/@{username}/video/{video_id}"
            
            desc = video.as_dict.get('desc', '')[:50]
            stats = video.stats
            likes = stats.get('diggCount', 0) if stats else 0
            
            video_list.append({
                'id': video_id,
                'url': url,
                'desc': desc,
                'likes': likes
            })
            
            if VERBOSE:
                print(f"  [{len(video_list)}] {video_id} - {desc}... (👍 {likes})")
        
        print(f"\n✓ 找到 {len(video_list)} 个视频\n")
        return video_list
    
    async def download_single_video(self, api, video_info, idx, total):
        """
        下载单个视频（带重试机制）
        
        参数:
            api: TikTokApi实例
            video_info: 视频信息字典
            idx: 当前索引
            total: 总数
        """
        video_id = video_info['id']
        url = video_info['url']
        
        print(f"\n[{idx}/{total}] 视频ID: {video_id}")
        print(f"描述: {video_info['desc']}...")
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            try:
                # 创建video对象并获取完整信息
                video = api.video(url=url)
                print(f"  → 获取视频信息...{f' (重试 {attempt + 1}/{MAX_RETRIES})' if attempt > 0 else ''}")
                video_data = await video.info()
                
                # 保存原始元数据到元数据文件夹
                metadata_file = os.path.join(
                    self.metadata_dir, 
                    METADATA_FILENAME_FORMAT.format(video_id=video_id)
                )
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(video_data, f, ensure_ascii=False, indent=2)
                
                # 清理元数据（如果启用）
                if CLEAN_METADATA:
                    cleaned_data = self.clean_metadata(video_data)
                    cleaned_file = os.path.join(
                        self.metadata_dir,
                        CLEANED_METADATA_FILENAME_FORMAT.format(video_id=video_id)
                    )
                    with open(cleaned_file, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                
                # 提取信息用于Excel
                excel_info = self.extract_video_info(video_data)
                
                # 显示统计信息
                stats = video_data.get('stats') or video_data.get('statsV2')
                if stats and VERBOSE:
                    print(f"  → 统计: 👍 {stats.get('diggCount', 0):,} | "
                          f"💬 {stats.get('commentCount', 0):,} | "
                          f"👁 {stats.get('playCount', 0):,}")
                
                # 下载视频到元数据文件夹
                print("  → 下载视频中...")
                video_bytes = await video.bytes()
                
                if video_bytes and len(video_bytes) > 10000:
                    video_file = os.path.join(
                        self.metadata_dir,
                        VIDEO_FILENAME_FORMAT.format(video_id=video_id)
                    )
                    with open(video_file, 'wb') as f:
                        f.write(video_bytes)
                    
                    size_mb = len(video_bytes) / (1024 * 1024)
                    print(f"  ✓ 下载成功: {VIDEO_FILENAME_FORMAT.format(video_id=video_id)} ({size_mb:.2f} MB)")
                    
                    # 更新Excel信息中的本地文件路径
                    excel_info['本地视频文件'] = VIDEO_FILENAME_FORMAT.format(video_id=video_id)
                    excel_info['视频文件大小(MB)'] = round(size_mb, 2)
                    excel_info['存储位置'] = METADATA_SUBDIR
                    
                    self.success_count += 1
                else:
                    print(f"  ✗ 下载失败: 文件太小或为空")
                    excel_info['本地视频文件'] = ''
                    excel_info['视频文件大小(MB)'] = 0
                    excel_info['存储位置'] = ''
                    self.fail_count += 1
                
                # 添加到汇总列表
                self.all_videos_info.append(excel_info)
                
                # 成功则跳出重试循环
                break
                        
            except Exception as e:
                error_msg = str(e)
                
                # 如果是最后一次尝试，记录失败
                if attempt == MAX_RETRIES - 1:
                    print(f"  ✗ 错误（已重试{MAX_RETRIES}次）: {error_msg}")
                    self.fail_count += 1
                    if not CONTINUE_ON_ERROR:
                        raise
                else:
                    # 还有重试机会，等待后重试
                    print(f"  ⚠️  错误: {error_msg}")
                    print(f"  ⏳ 等待 {RETRY_DELAY} 秒后重试...")
                    await asyncio.sleep(RETRY_DELAY)
    
    def generate_excel(self):
        """生成Excel汇总文件"""
        if not GENERATE_EXCEL or not self.all_videos_info:
            return
        
        print("\n" + "="*70)
        print("生成Excel汇总文件...")
        print("="*70)
        
        df = pd.DataFrame(self.all_videos_info)
        
        # 调整列顺序
        column_order = [col for col in EXCEL_COLUMNS if col in df.columns]
        df = df[column_order]
        
        # 保存Excel
        excel_file = os.path.join(self.output_dir, EXCEL_FILENAME)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        print(f"✓ Excel文件已生成: {excel_file}")
        print(f"  - 总行数: {len(df)}")
        print(f"  - 总列数: {len(df.columns)}")
        
        # 显示统计
        if VERBOSE and len(df) > 0:
            print(f"\n数据统计:")
            print(f"  - 总点赞数: {df['点赞数'].sum():,}")
            print(f"  - 总播放数: {df['播放数'].sum():,}")
            print(f"  - 平均点赞: {df['点赞数'].mean():.0f}")
            print(f"  - 平均播放: {df['播放数'].mean():.0f}")
    
    def print_summary(self):
        """打印下载总结"""
        print("\n" + "="*70)
        print("下载完成！")
        print("="*70)
        print(f"成功: {self.success_count} 个")
        print(f"失败: {self.fail_count} 个")
        print(f"\n文件存储位置:")
        print(f"  - 主目录: {self.output_dir}")
        print(f"  - 视频和元数据: {os.path.join(self.output_dir, METADATA_SUBDIR)}")
        print(f"  - 转录数据: {os.path.join(self.output_dir, TRANSCRIPTION_SUBDIR)} (待处理)")
        if GENERATE_EXCEL:
            print(f"  - Excel汇总: {os.path.join(self.output_dir, EXCEL_FILENAME)}")
        print("="*70)
    
    async def run(self):
        """运行下载器"""
        # 创建输出目录
        self.setup_output_dir()
        
        async with TikTokApi() as api:
            print("正在创建浏览器会话...")
            await api.create_sessions(
                ms_tokens=[MS_TOKEN] if MS_TOKEN else [None],
                num_sessions=NUM_SESSIONS,
                sleep_after=SLEEP_AFTER,
                headless=HEADLESS_MODE,
                browser=BROWSER_TYPE
            )
            print("✓ 会话创建成功\n")
            
            # 收集视频列表
            video_list = await self.collect_video_list(api)
            
            # 下载视频
            print("="*70)
            print("开始下载视频...")
            print("="*70)
            
            for idx, video_info in enumerate(video_list, 1):
                await self.download_single_video(api, video_info, idx, len(video_list))
                
                # 在视频之间添加延迟，避免被检测为机器人
                if idx < len(video_list) and SLEEP_BETWEEN_VIDEOS > 0:
                    if VERBOSE:
                        print(f"\n⏳ 等待 {SLEEP_BETWEEN_VIDEOS} 秒后继续...")
                    await asyncio.sleep(SLEEP_BETWEEN_VIDEOS)
            
            # 生成Excel
            self.generate_excel()
            
            # 打印总结
            self.print_summary()


def check_dependencies():
    """检查依赖库"""
    try:
        import pandas
        import openpyxl
    except ImportError:
        print("⚠️  缺少依赖库，正在安装...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pandas', 'openpyxl'])
        print("✓ 依赖安装完成\n")


def main():
    """主函数"""
    print("="*70)
    print("TikTok 视频下载器 - 整合版")
    print("="*70)
    print("功能:")
    print("  1. 下载视频和元数据")
    print("  2. 自动清理元数据（减小文件大小）")
    print("  3. 生成Excel汇总文件")
    print("="*70)
    print()
    
    # 检查依赖
    check_dependencies()
    
    # 检查ms_token
    if not MS_TOKEN and VERBOSE:
        print("⚠️  警告: 未设置 ms_token 环境变量")
        print("   如果下载失败，请设置: export ms_token='你的值'")
        print()
    
    # 显示配置
    print(f"配置:")
    print(f"  - 目标用户: @{TARGET_USERNAME}")
    print(f"  - 下载数量: {MAX_VIDEOS}")
    print(f"  - 输出目录: {OUTPUT_DIR}")
    print(f"  - 清理元数据: {'是' if CLEAN_METADATA else '否'}")
    print(f"  - 生成Excel: {'是' if GENERATE_EXCEL else '否'}")
    print()
    
    # 创建下载器并运行
    downloader = TikTokDownloader(
        username=TARGET_USERNAME,
        max_videos=MAX_VIDEOS,
        output_dir=OUTPUT_DIR
    )
    
    asyncio.run(downloader.run())


if __name__ == "__main__":
    main()
