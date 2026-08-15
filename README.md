# ROS 2 TurtleBot3 Navigation
## 1. 项目概览

本项目在 Ubuntu 22.04 虚拟机上，基于 ROS 2 Humble 为 TurtleBot3 (Burger) 搭建了一套完整的导航与自主探索系统。系统涵盖了基础的 SLAM 建图与路径规划，并进一步实现了 RGB-D 视觉感知、自定义底层规划器开发以及纯无人的前沿探索建图。


---

## 2. 核心架构与目录

本项目工作空间 (`ros2_ws`) 的核心目录结构如下：

*   `config/`: 存放 RViz2 视图配置及 Cartographer 建图规则文件。
*   `launch/`: 存放启动仿真环境、状态发布、建图与导航的核心 `.launch.py` 文件。
*   `maps/`: 存放跑图完成后，保存下来的高精度二维栅格地图文件（`.yaml` 与 `.pgm`）。
*   `scripts/`: 存放自己编写的 Python 逻辑脚本（如多点巡航 Action 客户端、YOLOv5 视觉推理节点）。
*   `urdf/`: 存放自定义的机器人统一描述文件，用于定义加装相机的物理坐标。
*   `my_nav2_params.yaml`: 自定义的 Nav2 导航栈参数文件，用于注入自定义 C++ A* 插件及调整安全膨胀半径。

---

## 3. 基础任务板块

本部分主要完成建图与导航的基础闭环。由于 ROS 2 的多节点特性，每个任务的命令需要在独立的终端中运行。

### 📍 任务一：物理仿真环境搭建与状态发布

*   **主要任务：** 拉起虚拟物理世界与小车实体，并持续向系统广播小车的 TF 坐标系骨架。
*   **实现逻辑与配置说明：** 将环境拉起与状态发布分在两个终端运行。为了解决 Gazebo 物理时间与 ROS 节点时间不同步导致的里程计报错问题，统一下发了 `use_sim_time:=true` 参数。每次运行前通过 `export` 声明模型类型。

**运行指令：**

```bash
# 终端 1
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch my_robot_env env_launch.py
```

```bash
# 终端 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo robot_state_publisher.launch.py use_sim_time:=true
```

---

### 📍 任务二：高精度 SLAM 建图 (Cartographer)

*   **主要任务：** 开启 SLAM 算法，通过键盘遥控小车走遍迷宫，处理雷达数据并把地图保存到本地。
*   **实现逻辑与配置说明：** 基于图优化理论，前端利用雷达扫描匹配，后端进行回环检测。探索完成后，利用 `map_saver_cli` 节点将内存里的栅格图输出为文件。配置上需要提前在包目录下新建好 `maps/` 文件夹来存放生成的地图。

**运行指令：**

```bash
# 终端 3
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true
```

```bash
# 终端 4
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```

```bash
# 终端 5 (建图闭合后执行)
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/my_robot_env/maps/my_map_carto
```

---

### 📍 任务三：Nav2 自主导航与动态避障

*   **主要任务：** 导入刚建好的静态地图，让小车实现自动路径规划与动态避障。
*   **实现逻辑与配置说明：** 启动 Nav2 行为树导航栈，全局采用 A* 算法寻路，局部采用 DWB 算法避开动态障碍物，并配合 AMCL 粒子滤波实现自我定位。配置上，启动命令中必须通过 `map` 参数指明加载 `my_map_carto.yaml` 地图文件。启动后，需要在 RViz2 中使用 "2D Pose Estimate" 工具给小车标定一次初始位姿。

**运行指令：**

```bash
# 终端 3
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true map:=/home/orange/ros2_ws/src/my_robot_env/maps/my_map_carto.yaml
```

---

### 📍 任务四：多目标点自动巡航 (Action Client)

*   **主要任务：** 编写代码实现小车在多个坐标点之间全自动循环巡逻。
*   **实现逻辑与配置说明：** 用 Python 编写 ROS 2 Action 客户端，与 Nav2 的动作服务器通信，异步发送目标点列表并实时读取执行反馈。运行前需要使用 `chmod +x` 给 Python 脚本赋予可执行权限。

**运行指令：**

```bash
# 终端 4
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
chmod +x ~/ros2_ws/src/my_robot_env/scripts/multi_waypoint_nav.py
python3 ~/ros2_ws/src/my_robot_env/scripts/multi_waypoint_nav.py
```

---

## 4. 高级任务板块

这部分在基础功能之上，对视觉感知、底层规划算法和全自动决策机制进行了开发和替换。

### 🚀 高级任务一：RGB-D 深度相机集成与验证

*   **主要任务：** 给小车模型加装 RGB-D 深度相机，并在仿真环境中打通图像数据流。
*   **实现逻辑与配置说明：** 修改小车的 URDF 文件，用 `<joint>` 标签把相机固定在底盘上方，同时挂载 Gazebo 插件，将环境的光学渲染转化为标准图像话题。在配置上，更新了包的 `setup.py` 文件，把新建的 launch 文件和 urdf 目录加入打包规则，确保系统编译时能载入新模型。

**运行指令：**

```bash
# 终端 1
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch my_robot_env spawn_rgbd_robot.launch.py
```

```bash
# 终端 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run rqt_image_view rqt_image_view
ros2 topic list
```

---

### 🚀 高级任务二：自定义 C++ A* 规划器接入

*   **主要任务：** 弃用系统自带算法，换上自己编写的 C++ A* (A-Star) 全局规划器。
*   **实现逻辑与配置说明：** 继承 Nav2 Pluginlib 核心基类编写代码。算法深度融合了代价地图 (Costmap)，通过识别膨胀区和未知盲区惩罚项，确保规划出的路线不会贴墙或进入盲区。在配置上，修改了 `my_nav2_params.yaml` 文件，通过参数将全局规划器的指针重定向到编译好的自定义动态链接库。执行前需清理后台无用进程以防冲突。

**运行指令：**

```bash
# 终端 1
killall -9 gzserver gzclient rviz2 2>/dev/null
cd ~/ros2_ws
colcon build --packages-select my_custom_planner
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch ~/ros2_ws/src/my_robot_env/launch/spawn_rgbd_robot.launch.py
```

```bash
# 终端 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true map:=/home/orange/ros2_ws/src/my_robot_env/maps/my_map_carto.yaml params_file:=/home/orange/ros2_ws/src/my_robot_env/my_nav2_params.yaml
```

---

### 🚀 高级任务三：YOLOv5 视觉节点部署

*   **主要任务：** 利用深度相机，让小车实现第一视角的实时物体检测与识别。
*   **实现逻辑与配置说明：** 通过 `cv_bridge` 将 ROS 2 图像转换为 NumPy 矩阵输入给 YOLOv5 模型。为了不影响底层的导航算力，将其作为一个独立的 Python 进程运行。针对虚拟机性能限制，在节点代码中将图像订阅协议修改为了 `sensor_data` (尽力而为，丢弃拥堵的旧帧)，并改为读取本地离线的 `.pt` 权重文件，解决了加载慢和画面卡死的问题。

**运行指令：**

```bash
# 终端 1
killall -9 gzserver gzclient rviz2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch my_robot_env spawn_rgbd_robot.launch.py
```

```bash
# 终端 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo robot_state_publisher.launch.py use_sim_time:=true
```

```bash
# 终端 3
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
python3 ~/ros2_ws/src/my_robot_env/scripts/yolo_vision_node.py
```

```bash
# 终端 4
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```

---

### 🚀 高级任务四：Explore Lite 纯自主探图

*   **主要任务：** 让小车自动寻找未知区域，完成全自动的迷宫探索和建图。
*   **实现逻辑与配置说明：** Cartographer 在后台边走边建图，无底图模式的 Nav2 负责避障。Explore Lite 算法通过寻找已知安全区与未知黑暗区的交界线（Frontier），不断把最优目标点发给 Nav2。因为迷宫走廊较窄，在终端 4 中使用 `ros2 param set` 动态调小了 `robot_radius` 和 `inflation_radius` 进行“瘦身”以防死锁。同时在探索节点启动命令中硬编码 `-p robot_base_frame:=base_footprint` 对齐车身坐标。

**运行指令：**

```bash
# 终端 1
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch my_robot_env env_launch.py
```

```bash
# 终端 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo robot_state_publisher.launch.py use_sim_time:=true
```

```bash
# 终端 3
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true
```

```bash
# 终端 4
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
ros2 param set /global_costmap/global_costmap robot_radius 0.11
ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.2
ros2 param set /local_costmap/local_costmap robot_radius 0.11
ros2 param set /local_costmap/local_costmap inflation_layer.inflation_radius 0.2
```

```bash
# 终端 5
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run explore_lite explore --ros-args -p use_sim_time:=true -p costmap_topic:=/global_costmap/costmap -p robot_base_frame:=base_footprint -p min_frontier_size:=0.2 -p visualize:=true
```
