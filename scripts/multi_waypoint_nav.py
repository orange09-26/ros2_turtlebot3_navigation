#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus
import math

class MultiWaypointNavigator(Node):
    def __init__(self):
        super().__init__('multi_waypoint_navigator')
        
        # 1. 创建动作客户端，连接到 Nav2 的 navigate_to_pose 服务器
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # 2. 定义你要去的 5 个真实目标点坐标 (x, y, yaw_angle)
        self.waypoints = [
            (3.09, -0.907, 0.0),    # 目标点 1 (图一)
            (0.893, -2.21, 0.0),    # 目标点 2 (图二)
            (0.493, -1.16, 0.0),    # 目标点 3 (图三)
            (-1.64, -3.72, 0.0),    # 目标点 4 (图四)
            (-0.851, 1.97, 0.0)     # 目标点 5 (图五)
        ]
        self.current_goal_index = 0

        # 3. 阻塞等待服务器启动
        self.get_logger().info('⏳ 等待 Nav2 导航服务器启动...')
        self._action_client.wait_for_server()
        self.get_logger().info('✅ 导航服务器已连接！准备开始自动巡航。')

        # 4. 触发第一个点
        self.send_next_goal()

    def send_next_goal(self):
        """发送队列中的下一个目标点"""
        if self.current_goal_index < len(self.waypoints):
            x, y, yaw = self.waypoints[self.current_goal_index]
            self.get_logger().info(f'🚀 正在前往目标点 {self.current_goal_index + 1}/{len(self.waypoints)}: [x={x:.2f}, y={y:.2f}]')
            self.send_goal(x, y, yaw)
        else:
            self.get_logger().info('🎉 太棒了！所有 5 个目标点均已成功到达！多点自动巡航任务完美结束。')
            rclpy.shutdown()

    def send_goal(self, x, y, yaw):
        """构建目标消息并发送给 Nav2"""
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self.create_pose_stamped(x, y, yaw)

        # 异步发送目标点，并绑定“服务器响应”回调函数
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def create_pose_stamped(self, x, y, yaw):
        """辅助函数：将简单的 x, y, yaw 转换为 ROS2 导航所需的 PoseStamped 消息格式"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        # 设定坐标位置
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0

        # 简单的欧拉角 (yaw) 转四元数 (只绕 Z 轴旋转)
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        return pose

    def goal_response_callback(self, future):
        """回调函数 1：处理服务器是否接受了我们的目标点"""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'❌ 目标点 {self.current_goal_index + 1} 被导航服务器拒绝！可能坐标在墙里或者无法到达。')
            return

        self.get_logger().info(f'🟢 目标点 {self.current_goal_index + 1} 已被接受，Nav2 正在全自动驾驶中...')
        
        # 目标接受后，绑定“导航完成结果”回调函数
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """回调函数 2：处理到达目标点后的最终结果"""
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'📍 成功精准到达目标点 {self.current_goal_index + 1}！\n' + '-'*40)
        else:
            self.get_logger().warn(f'⚠️ 目标点 {self.current_goal_index + 1} 导航异常中断或失败，状态码: {status}\n' + '-'*40)

        # 无论当前点成功与否，继续强行前往下一个点
        self.current_goal_index += 1
        self.send_next_goal()


def main(args=None):
    rclpy.init(args=args)
    navigator = MultiWaypointNavigator()
    
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        navigator.get_logger().info('收到中断信号 (Ctrl+C)，强制停止导航节点。')
    finally:
        # 清理并关闭节点
        if rclpy.ok():
            navigator.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
