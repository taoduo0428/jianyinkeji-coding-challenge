"""
视频转录器 - 使用 faster-whisper
功能：
1. 批量转录视频为文字
2. 支持多种输出格式
3. 自动跳过已处理的文件
4. 显示详细进度
"""
import os
import time
from pathlib import Path
from transcription_config import *

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("错误: 未安装 faster-whisper")
    print("请运行: pip install faster-whisper")
    exit(1)


class VideoTranscriber:
    """视频转录器类"""
    
    def __init__(self, input_dir=INPUT_DIR, output_dir=OUTPUT_DIR):
        """
        初始化转录器
        
        参数:
            input_dir: 输入目录（视频所在位置）
            output_dir: 输出目录（转录结果保存位置）
        """
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 转换为绝对路径
        self.input_dir = os.path.join(script_dir, input_dir) if not os.path.isabs(input_dir) else input_dir
        self.output_dir = os.path.join(script_dir, output_dir) if not os.path.isabs(output_dir) else output_dir
        
        self.model = None
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
    def setup_output_dir(self):
        """创建输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            if VERBOSE:
                print(f"✓ 创建输出目录: {self.output_dir}\n")
        else:
            if VERBOSE:
                print(f"✓ 使用输出目录: {self.output_dir}\n")
    
    def load_model(self):
        """加载 Whisper 模型"""
        if VERBOSE:
            print(f"正在加载 Whisper 模型...")
            print(f"  - 模型大小: {MODEL_SIZE}")
            print(f"  - 设备: {DEVICE}")
            print(f"  - 计算类型: {COMPUTE_TYPE}")
        
        try:
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            if VERBOSE:
                print(f"✓ 模型加载成功\n")
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            print("\n提示:")
            print("  - 如果是 CUDA 错误，请尝试使用 device='cpu'")
            print("  - 如果是内存不足，请尝试使用更小的模型（如 'base' 或 'tiny'）")
            raise
    
    def get_video_files(self):
        """获取所有视频文件"""
        video_files = []
        
        if not os.path.exists(self.input_dir):
            print(f"✗ 输入目录不存在: {self.input_dir}")
            return video_files
        
        for file in os.listdir(self.input_dir):
            if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                video_files.append(os.path.join(self.input_dir, file))
        
        # 限制处理数量
        if MAX_VIDEOS is not None and len(video_files) > MAX_VIDEOS:
            video_files = video_files[:MAX_VIDEOS]
        
        return sorted(video_files)
    
    def get_output_filename(self, video_path):
        """生成输出文件名"""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        if OUTPUT_FORMAT == "txt":
            return f"{video_name}_transcript.txt"
        elif OUTPUT_FORMAT == "srt":
            return f"{video_name}_transcript.srt"
        elif OUTPUT_FORMAT == "vtt":
            return f"{video_name}_transcript.vtt"
        elif OUTPUT_FORMAT == "json":
            return f"{video_name}_transcript.json"
        else:
            return f"{video_name}_transcript.txt"
    
    def format_timestamp(self, seconds):
        """格式化时间戳"""
        if TIMESTAMP_FORMAT == "seconds":
            return f"{seconds:.2f}s"
        else:  # time format
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def format_segment_txt(self, segment):
        """格式化片段为TXT格式"""
        if INCLUDE_TIMESTAMPS:
            start = self.format_timestamp(segment.start)
            end = self.format_timestamp(segment.end)
            return f"[{start} -> {end}] {segment.text}\n"
        else:
            return f"{segment.text}\n"
    
    def format_segment_srt(self, index, segment):
        """格式化片段为SRT格式"""
        def format_srt_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        start = format_srt_time(segment.start)
        end = format_srt_time(segment.end)
        return f"{index}\n{start} --> {end}\n{segment.text}\n\n"
    
    def format_segment_vtt(self, segment):
        """格式化片段为VTT格式"""
        def format_vtt_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        
        start = format_vtt_time(segment.start)
        end = format_vtt_time(segment.end)
        return f"{start} --> {end}\n{segment.text}\n\n"
    
    def transcribe_video(self, video_path):
        """
        转录单个视频
        
        参数:
            video_path: 视频文件路径
        """
        video_name = os.path.basename(video_path)
        output_filename = self.get_output_filename(video_path)
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 检查是否已存在
        if SKIP_EXISTING and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 0:
                if VERBOSE:
                    print(f"  ⏭️  跳过（已存在）: {output_filename} ({file_size} bytes)")
                self.skip_count += 1
                return True
        
        if VERBOSE:
            print(f"  → 开始转录: {video_name}")
        
        start_time = time.time()
        
        try:
            # 转录视频
            segments, info = self.model.transcribe(
                video_path,
                beam_size=BEAM_SIZE,
                language=LANGUAGE,
                initial_prompt=INITIAL_PROMPT
            )
            
            if VERBOSE:
                print(f"  → 检测到的语言: {info.language} (概率: {info.language_probability:.2f})")
                print(f"  → 视频时长: {info.duration:.1f} 秒")
            
            # 保存转录结果
            with open(output_path, 'w', encoding='utf-8') as f:
                if OUTPUT_FORMAT == "vtt":
                    f.write("WEBVTT\n\n")
                
                last_print_time = time.time()
                segment_count = 0
                
                for i, segment in enumerate(segments, 1):
                    segment_count = i
                    
                    # 根据格式写入
                    if OUTPUT_FORMAT == "txt":
                        f.write(self.format_segment_txt(segment))
                    elif OUTPUT_FORMAT == "srt":
                        f.write(self.format_segment_srt(i, segment))
                    elif OUTPUT_FORMAT == "vtt":
                        f.write(self.format_segment_vtt(segment))
                    elif OUTPUT_FORMAT == "json":
                        import json
                        f.write(json.dumps({
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text
                        }, ensure_ascii=False) + "\n")
                    
                    # 显示进度
                    if VERBOSE and (i % PROGRESS_FREQUENCY == 0 or 
                                   time.time() - last_print_time >= PROGRESS_INTERVAL):
                        progress = (segment.end / info.duration) * 100 if info.duration > 0 else 0
                        print(f"  → 进度: {segment.end:.1f}s / {info.duration:.1f}s ({progress:.1f}%)")
                        last_print_time = time.time()
            
            # 计算统计信息
            end_time = time.time()
            transcription_time = end_time - start_time
            speedup_factor = info.duration / transcription_time if transcription_time > 0 else 0
            
            if VERBOSE:
                print(f"  ✓ 转录完成: {output_filename}")
                print(f"    - 片段数: {segment_count}")
                print(f"    - 转录耗时: {transcription_time:.1f} 秒")
                print(f"    - 加速比: {speedup_factor:.1f}X")
            
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"  ✗ 转录失败: {str(e)}")
            self.fail_count += 1
            if not CONTINUE_ON_ERROR:
                raise
            return False
    
    def run(self):
        """运行批量转录"""
        # 创建输出目录
        self.setup_output_dir()
        
        # 加载模型
        self.load_model()
        
        # 获取视频文件
        video_files = self.get_video_files()
        
        if not video_files:
            print(f"✗ 在 {self.input_dir} 中未找到视频文件")
            return
        
        print(f"找到 {len(video_files)} 个视频文件")
        print("="*70)
        print("开始转录...")
        print("="*70)
        print()
        
        # 逐个转录
        for idx, video_path in enumerate(video_files, 1):
            print(f"[{idx}/{len(video_files)}] {os.path.basename(video_path)}")
            self.transcribe_video(video_path)
            print()
        
        # 打印总结
        self.print_summary()
    
    def print_summary(self):
        """打印转录总结"""
        print("="*70)
        print("转录完成！")
        print("="*70)
        print(f"成功: {self.success_count} 个")
        print(f"跳过: {self.skip_count} 个")
        print(f"失败: {self.fail_count} 个")
        print(f"\n文件位置:")
        print(f"  - 输入目录: {self.input_dir}")
        print(f"  - 输出目录: {self.output_dir}")
        print("="*70)


def check_dependencies():
    """检查依赖库"""
    try:
        import faster_whisper
    except ImportError:
        print("="*70)
        print("缺少依赖库: faster-whisper")
        print("="*70)
        print("\n请安装以下依赖:")
        print("\n  pip install faster-whisper\n")
        print("如果使用GPU加速，还需要安装:")
        print("\n  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118\n")
        print("="*70)
        return False
    return True


def main():
    """主函数"""
    print("="*70)
    print("视频转录器 - 基于 faster-whisper")
    print("="*70)
    print()
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 显示配置
    print("配置:")
    print(f"  - 输入目录: {INPUT_DIR}")
    print(f"  - 输出目录: {OUTPUT_DIR}")
    print(f"  - 模型大小: {MODEL_SIZE}")
    print(f"  - 设备: {DEVICE}")
    print(f"  - 输出格式: {OUTPUT_FORMAT}")
    print(f"  - 包含时间戳: {'是' if INCLUDE_TIMESTAMPS else '否'}")
    print()
    
    # 创建转录器并运行
    transcriber = VideoTranscriber(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR
    )
    
    transcriber.run()


if __name__ == "__main__":
    main()
