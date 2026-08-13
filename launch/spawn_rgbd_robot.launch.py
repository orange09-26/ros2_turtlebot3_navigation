import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    gazebo_ros_pkg = get_package_share_directory('gazebo_ros')
    
    # 切断僵尸网络，防止 Gazebo 卡死
    os.environ["GAZEBO_MODEL_DATABASE_URI"] = ""
    
    # 1. 启动 Gazebo，并强制加载你确定的 my_world2.world 迷宫！
    world_path = '/home/orange/ros2_ws/src/my_robot_env/worlds/my_world2.world'
    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros_pkg, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': world_path}.items()
    )
    
    # 读取你的 URDF 模型文件内容
    urdf_file_path = '/home/orange/ros2_ws/src/my_robot_env/urdf/my_robot_rgbd.urdf'
    with open(urdf_file_path, 'r') as infp:
        robot_desc = infp.read()
        
    # 2. 启动骨架发布者 (保证 RViz 里能看见小车)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}],
        output='screen'
    )
    
    # 3. 投放小车 (以地图原点为准，如果你发现小车卡在墙里，可以自行微调 x 和 y 的坐标)
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'my_rgbd_turtlebot', '-file', urdf_file_path, '-x', '0.0', '-y', '0.0', '-z', '0.05'],
        output='screen'
    )
    
    return LaunchDescription([
        start_gazebo,
        robot_state_publisher_node,
        spawn_robot
    ])
