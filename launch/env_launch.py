import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 获取我们功能包的路径
    pkg_share = get_package_share_directory('my_robot_env')
    # 找到刚刚保存的 world 文件路径
    world_path = os.path.join(pkg_share, 'worlds', 'my_world2.world')

    # 启动 Gazebo 及其 ROS 2 插件
    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_path],
        output='screen'
    )

    # 借用官方的 launch 文件，把 TurtleBot3 机器人“召唤”到坐标 (0,0,0) 的位置
    tb3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    spawn_tb3 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3_gazebo_dir, 'launch', 'spawn_turtlebot3.launch.py')),
        launch_arguments={'x_pose': '0.0', 'y_pose': '0.0', 'z_pose': '0.1'}.items()
    )

    return LaunchDescription([
        gazebo,
        spawn_tb3
    ])
