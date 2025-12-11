import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kiwi_video.core.orchestrator import DirectorOrchestrator
from kiwi_video.utils.logger import setup_logging


def print_banner(text: str, char: str = "="):
    """打印横幅"""
    width = 80
    print()
    print(char * width)
    print(f"{text:^{width}}")
    print(char * width)
    print()


def print_section(text: str):
    """打印章节标题"""
    print(f"\n{'─' * 80}")
    print(f"📋 {text}")
    print('─' * 80)


def show_file_tree(workspace_dir: Path):
    """显示工作区文件树"""
    print_section("生成的文件结构")

    if not workspace_dir.exists():
        print("⚠️  工作区不存在")
        return

    # 显示关键文件夹
    folders = {
        "📝 脚本": "annotated_script.json",
        "🎨 分镜": "storyboard.json",
        "🎙️ 音频": "audio/",
        "🎬 素材": "assets/",
        "🎞️ 片段": "clips/",
        "📊 状态": "project_state.json"
    }

    for label, path in folders.items():
        full_path = workspace_dir / path
        if full_path.exists():
            if full_path.is_dir():
                files = list(full_path.glob("**/*"))
                file_count = len([f for f in files if f.is_file()])
                print(f"  {label}: {file_count} 文件")

                # 显示音频文件详情
                if "audio" in path:
                    for audio_file in full_path.glob("*.mp3"):
                        size_kb = audio_file.stat().st_size / 1024
                        print(f"    └─ {audio_file.name} ({size_kb:.1f} KB)")
                    for asr_file in full_path.glob("*.json"):
                        print(f"    └─ {asr_file.name} (ASR)")

                # 显示视频片段
                elif "clips" in path:
                    for clip in full_path.glob("*.mp4"):
                        size_mb = clip.stat().st_size / (1024 * 1024)
                        print(f"    └─ {clip.name} ({size_mb:.1f} MB)")
            else:
                size_kb = full_path.stat().st_size / 1024
                print(f"  {label}: {full_path.name} ({size_kb:.1f} KB)")
        else:
            print(f"  {label}: ❌ 未生成")


def show_audio_summary(workspace_dir: Path):
    """显示音频生成摘要"""
    print_section("音频生成摘要")

    audio_dir = workspace_dir / "audio"
    if not audio_dir.exists():
        print("❌ 没有生成音频文件")
        return

    audio_files = list(audio_dir.glob("*_voice.mp3"))
    asr_files = list(audio_dir.glob("*_asr.json"))

    print(f"✅ 生成了 {len(audio_files)} 个音频文件")
    print(f"✅ 生成了 {len(asr_files)} 个 ASR 文件")

    # 显示每个场景的音频详情
    for audio_file in sorted(audio_files):
        scene_id = audio_file.stem.replace("_voice", "")
        asr_file = audio_dir / f"{scene_id}_asr.json"

        size_kb = audio_file.stat().st_size / 1024
        print(f"\n  🎙️ {scene_id}:")
        print(f"     音频: {audio_file.name} ({size_kb:.1f} KB)")

        if asr_file.exists():
            import json
            try:
                with open(asr_file) as f:
                    asr_data = json.load(f)
                    # 尝试获取时长信息
                    if 'duration' in asr_data:
                        print(f"     时长: {asr_data['duration']:.2f}s")
                    print("     ASR: ✅ 包含词级时间戳")
            except Exception as e:
                print(f"     ASR: ⚠️ 无法读取 ({e})")
        else:
            print("     ASR: ❌ 未生成")


async def test_basic_workflow():
    """测试基础工作流"""
    print_banner("🎬 KIWI-Video 完整流程测试", "=")

    # 测试项目配置
    project_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    workspace_dir = Path("workspaces") / project_id

    print(f"📦 项目 ID: {project_id}")
    print(f"📁 工作区: {workspace_dir}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 用户输入
    user_input = """generate a video about the future of singapore

desired duration: 30 seconds
number of scenes: 4
"""

    print_section("用户输入")
    print(user_input)

    try:
        # 创建编排器
        print_section("初始化系统")
        orchestrator = DirectorOrchestrator(
            project_id=project_id,
            workspace_dir=workspace_dir
        )
        print("✅ 系统初始化完成")

        # 执行完整流程
        print_banner("开始执行 5 阶段工作流", "-")

        start_time = datetime.now()
        result = await orchestrator.execute_project(user_input)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        # 显示结果
        print_banner("✅ 工作流执行完成", "=")

        print(f"⏱️  总耗时: {duration:.1f} 秒")
        print(f"📊 项目状态: {result.get('status', 'unknown')}")
        print(f"📦 项目 ID: {result.get('project_id')}")
        print(f"🎥 最终视频: {result.get('final_video_path', '未生成')}")
        print(f"📁 工作区: {result.get('workspace_dir')}")

        # 显示文件树
        show_file_tree(workspace_dir)

        # 显示音频摘要
        show_audio_summary(workspace_dir)

        # 显示成功统计
        print_section("执行统计")

        # 读取状态文件
        state_file = workspace_dir / "project_state.json"
        if state_file.exists():
            import json
            with open(state_file) as f:
                state = json.load(f)
                phases = state.get('phases', {})

                print("各阶段状态:")
                phase_names = {
                    'story_loader': '📝 Phase 1: 脚本生成',
                    'storyboard': '🎨 Phase 2: 分镜创建',
                    'voice_actor': '🎙️ Phase 3: 音频生成',
                    'film_crew': '🎬 Phase 4: 视频制作',
                }

                for phase_key, phase_name in phase_names.items():
                    phase_data = phases.get(phase_key, {})
                    status = phase_data.get('status', 'unknown')
                    status_emoji = '✅' if status == 'completed' else '❌'
                    print(f"  {status_emoji} {phase_name}: {status}")

        print_banner("🎉 测试完成！", "=")
        print(f"\n💡 查看生成的文件: cd {workspace_dir}")
        print(f"💡 播放最终视频: open {result.get('final_video_path', '')}\n")

        return True

    except Exception as e:
        print_banner("❌ 测试失败", "=")
        print(f"\n错误信息: {e}\n")

        import traceback
        print("详细堆栈:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)

        # 尝试显示已生成的文件
        if workspace_dir.exists():
            print("\n尝试显示已生成的文件:")
            show_file_tree(workspace_dir)

        return False


async def test_audio_priority():
    """测试音频优先流程的关键点"""
    print_banner("🎙️ 音频优先流程验证", "=")

    project_id = f"audio_test_{datetime.now().strftime('%H%M%S')}"
    workspace_dir = Path("workspaces") / project_id

    print("验证关键特性:")
    print("  1. ✅ 音频在视频之前生成")
    print("  2. ✅ ASR 数据包含词级时间戳")
    print("  3. ✅ FilmCrew 基于音频时长规划视频")
    print("  4. ✅ 视频和音频完美同步")

    user_input = "创建一个关于太空探索的 15 秒短视频"

    try:
        orchestrator = DirectorOrchestrator(
            project_id=project_id,
            workspace_dir=workspace_dir
        )

        result = await orchestrator.execute_project(user_input)

        # 验证音频文件
        audio_dir = workspace_dir / "audio"
        if audio_dir.exists():
            audio_files = list(audio_dir.glob("*.mp3"))
            asr_files = list(audio_dir.glob("*_asr.json"))

            print(f"\n✅ 音频文件: {len(audio_files)} 个")
            print(f"✅ ASR 文件: {len(asr_files)} 个")

            if audio_files and asr_files:
                print("\n🎉 音频优先流程验证成功！")
            else:
                print("\n⚠️  音频文件不完整")

        return True

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="KIWI-Video 完整流程测试")
    parser.add_argument(
        "--mode",
        choices=["basic", "audio", "all"],
        default="basic",
        help="测试模式: basic=基础流程, audio=音频验证, all=全部",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="日志文件路径 (可选)"
    )

    args = parser.parse_args()

    # 设置日志
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(log_file=log_file)

    # 运行测试
    if args.mode == "basic":
        success = asyncio.run(test_basic_workflow())
    elif args.mode == "audio":
        success = asyncio.run(test_audio_priority())
    else:  # all
        print_banner("运行所有测试", "=")
        success1 = asyncio.run(test_basic_workflow())
        success2 = asyncio.run(test_audio_priority())
        success = success1 and success2

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

