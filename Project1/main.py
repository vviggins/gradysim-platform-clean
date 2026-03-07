from gradysim.simulator.handler.communication import CommunicationHandler, CommunicationMedium
from gradysim.simulator.handler.mobility import MobilityHandler
from gradysim.simulator.handler.timer import TimerHandler
from gradysim.simulator.handler.visualization import VisualizationHandler
from gradysim.simulator.simulation import SimulationBuilder, SimulationConfiguration
from protocol_sensor import SimpleProtocolSensor
from protocol_mobile import SimpleProtocolMobile
from protocol_ground import SimpleProtocolGround

# 全局变量，用于传递参数给无人机协议
_mobile_params = None

def add_sensors_from_file(builder, file_path):
    """
    通过文件批量添加传感器节点。
    这个地方的传感器节点和无人机需要飞行路径的节点是相同的，也就是一一对应的。传感器节点的位置，就是无人机需要飞到的位置。

    参数:
        builder: 场景构建器对象
        file_path: 传感器坐标文件路径
    """
    try:
        scale_factor = 20  # 放大倍数，与无人机协议保持一致
        with open(file_path, 'r') as file:
            for line in file:
                # 解析 x, y, z 坐标，支持两种格式：空格分隔和逗号分隔
                parts = line.strip().replace(',', ' ').split()
                if len(parts) >= 2:
                    x = float(parts[0]) * scale_factor  # 放大x坐标
                    y = float(parts[1]) * scale_factor  # 放大y坐标
                    z = 0.0  # 二维数据，z坐标设为0
                    # 添加传感器节点
                    builder.add_node(SimpleProtocolSensor, (x, y, z))
        
        # 使用UTF-8编码输出
        import sys
        if sys.platform == 'win32':
            import os
            os.system('chcp 65001 >nul')
        print(f"传感器节点已成功加载自文件: {file_path}，放大倍数: {scale_factor}")

    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 未找到")
    except ValueError as e:
        print(f"错误: 文件 {file_path} 格式错误，每行应为 'x, y' 或 'x, y, z'")
        print(f"具体错误: {e}")

def run_simulation(real_time: bool, node_file_path=None, result_dir=None):
    """
    运行模拟
    
    参数:
        real_time: 是否实时运行
        node_file_path: 节点文件路径，如果为None则使用默认路径
        result_dir: 结果保存目录，如果为None则使用默认路径
    """
    # 使用脚本所在目录作为基准目录，后续无论是否传入自定义路径都能用到
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 设置默认节点文件路径
    if node_file_path is None:
        node_file_path = os.path.join(base_dir, "../../data/node50/data1001.txt")
    
    # 设置默认结果保存目录
    if result_dir is None:
        result_dir = './results'
    
    # 确保节点文件存在
    import os
    if not os.path.exists(node_file_path):
        print(f"错误: 节点文件 {node_file_path} 不存在")
        return
    
    print(f"开始模拟，节点文件: {node_file_path}")
    print(f"结果保存目录: {result_dir}")
    
    # 禁用可视化以避免多进程问题，同时禁用debug和execution_logging以避免生成大量CSV文件
    builder = SimulationBuilder(SimulationConfiguration(duration=100, debug=False, execution_logging=False, real_time=0))
    # 无干扰：关闭通信失败与传输延迟
    builder.add_handler(CommunicationHandler(CommunicationMedium(transmission_range=0.4, failure_rate=0.0, delay=0.0)))
    builder.add_handler(TimerHandler())
    builder.add_handler(MobilityHandler())

    # 禁用可视化处理器以避免多进程问题
    # if real_time:
    #     builder.add_handler(VisualizationHandler())

    # Ground location地面基站 一个就行
    builder.add_node(SimpleProtocolGround, (-6.9, 0.0, 0.0))

    # Drone locations无人机 目前一个就行
    # 提取节点文件名用于结果保存
    import os
    node_filename = os.path.basename(node_file_path).replace('.txt', '')
    
    # 不创建单独的文件夹，所有数据都保存在results目录下
    # result_dir = f"{result_dir}/node50_{node_filename}"
    # os.makedirs(result_dir, exist_ok=True)
    
    # 添加无人机节点
    # 使用全局变量存储参数，在protocol初始化时获取
    global _mobile_params
    _mobile_params = {
        "result_dir": result_dir,
        "node_file": node_filename,
        # 传递节点文件所在目录，便于协议层选择正确的 waypoint 文件夹
        "node_dir": os.path.dirname(os.path.abspath(node_file_path)),
    }
    
    builder.add_node(SimpleProtocolMobile, (0, 0.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-3.9000000000000004, -3.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-3.9000000000000004, 3.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-0.9000000000000004, -6.0, 0.0))

    # 从指定文件加载节点数据
    add_sensors_from_file(builder, node_file_path)

    # Simulation
    print("正在构建模拟...")
    simulation = builder.build()
    print("模拟构建完成，开始运行...")
    simulation.start_simulation()
    print("模拟运行完成")
    
    # 删除生成的CSV文件
    
    import glob
    csv_files = glob.glob(os.path.join(base_dir, "*.csv"))
    for csv_file in csv_files:
        try:
            os.remove(csv_file)
        except Exception as e:
            print(f"删除文件 {csv_file} 时出错: {e}")


if __name__ == '__main__':
    run_simulation(True)
