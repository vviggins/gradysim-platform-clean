from gradysim.simulator.handler.communication import CommunicationHandler, CommunicationMedium
from gradysim.simulator.handler.mobility import MobilityHandler
from gradysim.simulator.handler.timer import TimerHandler
from gradysim.simulator.handler.visualization import VisualizationHandler
from gradysim.simulator.simulation import SimulationBuilder, SimulationConfiguration
from protocol_sensor import SimpleProtocolSensor
from protocol_mobile import SimpleProtocolMobile
from protocol_ground import SimpleProtocolGround

def add_sensors_from_file(builder, file_path):
    """
    通过文件批量添加传感器节点。
    这个地方的传感器节点和无人机需要飞行路径的节点是相同的，也就是一一对应的。传感器节点的位置，就是无人机需要飞到的位置。

    参数:
        builder: 场景构建器对象
        file_path: 传感器坐标文件路径
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # 解析 x, y, z 坐标`
                x, y, z = map(float, line.strip().split(','))  
                # 添加传感器节点
                builder.add_node(SimpleProtocolSensor, (x, y, z))
        
        print(f"✅ 传感器节点已成功加载自文件: {file_path}")

    except FileNotFoundError:
        print(f" 错误: 文件 {file_path} 未找到")
    except ValueError:
        print(f" 错误: 文件 {file_path} 格式错误，每行应为 'x, y, z'")

def run_simulation(real_time: bool):
    builder = SimulationBuilder(SimulationConfiguration(duration=100, debug=True, real_time=30))
    builder.add_handler(CommunicationHandler(CommunicationMedium(transmission_range=0.4,failure_rate=0.5,delay = 0.005)))
    builder.add_handler(TimerHandler())
    builder.add_handler(MobilityHandler())

    if real_time:
        builder.add_handler(VisualizationHandler())

    # Ground location地面基站 一个就行
    builder.add_node(SimpleProtocolGround, (-6.9, 0.0, 0.0))

    # Drone locations无人机 目前一个就行
    builder.add_node(SimpleProtocolMobile, (0, 0.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-3.9000000000000004, -3.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-3.9000000000000004, 3.0, 0.0))
    # builder.add_node(SimpleProtocolMobile, (-0.9000000000000004, -6.0, 0.0))

    # 从这个地方加载TSP节点文件，也就是以源文件
    #读取点
    sensor_file = './waypoint/tsp_100_nodes_file1.txt'
    add_sensors_from_file(builder, sensor_file)

    # Simulation
    simulation = builder.build()
    simulation.start_simulation()


if __name__ == '__main__':
    run_simulation(True)
