from setuptools import find_packages, setup
import os               
from glob import glob   

package_name = 'my_robot_env'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # 1. 修复：把匹配规则改成 '*.py'，这样无论是 env_launch.py 还是 spawn_rgbd_robot.launch.py 都能被找到了！
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        
        # 2. 原本的 worlds 规则保持不变
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        
        # 3. 【新增】：将高级任务新加的 urdf 文件夹打包进去，否则会报模型找不到的错
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        
        # 4. 【新增】：将高级任务新加的自定义导航参数文件打包进去
        (os.path.join('share', package_name), ['my_nav2_params.yaml']),
        
        # 5. 【新增】：为防止以后出 bug，顺手把你建好的 maps 和 config 文件夹也加入打包规则
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orange',
    maintainer_email='orange@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
