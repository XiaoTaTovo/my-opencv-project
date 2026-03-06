import torch
from ultralytics import YOLO

def check_environment():
    print("-" * 30)
    # 1. 检查 PyTorch 版本和 GPU
    print(f"PyTorch 版本: {torch.__version__}")
    if torch.cuda.is_available():
        print("GPU 状态: 可用!")
        print(f"显卡型号: {torch.cuda.get_device_name(0)}")
        print(f"CUDA 版本: {torch.version.cuda}")
    else:
        print("GPU 状态: 不可用 (正在使用 CPU)")
        print("# 如果这里打印不可用，说明安装命令没对，或者驱动有问题")
    print("-" * 30)

    # 2. 测试 YOLO11
    # 第一次运行会自动下载 yolov11n.pt 模型文件
    print("正在加载 YOLO11 模型...")
    try:
        model = YOLO("yolo11n.pt")
        print("YOLO11 模型加载成功!")
        print("环境配置完美完成。")
    except Exception as e:
        print(f"YOLO 加载失败: {e}")

if __name__ == "__main__":
    check_environment()
