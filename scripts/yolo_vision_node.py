#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import torch

class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')
        
        # 1. 订阅小车摄像头的真实图像话题
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.listener_callback,
            10)
            
        # 2. 初始化 CV 翻译官
        self.br = CvBridge()
        
        # 3. 加载官方 YOLOv5s 轻量级预训练模型
        self.get_logger().info("🚀 正在从 PyTorch Hub 加载 YOLOv5 模型，请耐心等待 (首次运行需下载)...")
        # 使用 ultralytics 官方仓库的 yolov5s 模型
        self.model = torch.hub.load('/home/orange/.cache/torch/hub/ultralytics_yolov5_master', 'custom', path='/home/orange/yolov5s.pt', source='local')
        self.get_logger().info("✅ YOLOv5 模型加载完毕！等待接收图像流...")

    def listener_callback(self, data):
        try:
            # 步骤 A：将 ROS 图像转换为 OpenCV 图像
            current_frame = self.br.imgmsg_to_cv2(data, "bgr8")
            
            # 步骤 B：送入 YOLOv5 进行目标检测推理
            results = self.model(current_frame)
            
            # 步骤 C：将识别到的边界框和标签直接渲染到原图上
            results.render() 
            
            # 步骤 D：用 OpenCV 弹出窗口实时显示画面
            cv2.imshow("TurtleBot3 YOLOv5 Vision", current_frame)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'图像处理发生崩溃: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    rclpy.spin(node)
    
    # 关闭节点时清理窗口
    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
