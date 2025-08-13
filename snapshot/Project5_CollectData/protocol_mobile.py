# import logging
# import random
# from gradysim.protocol.plugin.mission_mobility import (
#     LoopMission,
#     MissionMobilityPlugin,
#     MissionMobilityConfiguration,
# )
# from gradysim.protocol.plugin.statistics import create_statistics, finish_statistics
# from gradysim.protocol.messages.communication import BroadcastMessageCommand

# from gradysim.protocol.messages.telemetry import Telemetry
# from gradysim.protocol.interface import IProtocol
# from message import SimpleMessage, SenderType
# from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand, SetSpeedMobilityCommand


# class SimpleProtocolMobile(IProtocol):
#     def __init__(self):
#         #以下是无人机自带的收集数据包相关内容
#         self.packets: int = 0

#         #以下是无人机自带的遥感信息
#         self.last_telemetry_message: Telemetry

#         #以下是无人机日志
#         self._logger = logging.getLogger()
#         self._logger.propagate = False

#         #以下是无人机电量相关内容
#         self.energy = 100  # 初始电池电量
#         self.low_energy_threshold = 20  # 低电量阈值
#         self.energy_consumption_rate = 3  # 每秒消耗3点电量
#         self.is_charging = False  # 是否正在充电
        

#     def initialize(self):
#         self._logger.debug("初始化无人机节点")
#         print(f"[DEBUG] UAV 初始电量: {self.energy}")



#         create_statistics(self)  #统计数据函数

#         self.mission: MissionMobilityPlugin= MissionMobilityPlugin(
#             self, MissionMobilityConfiguration(loop_mission=LoopMission.RESTART)
#         )


#         # 如果是刚接触这个项目的人，可以用添加这种简单的飞行点来熟悉，下面是用文件，文件里面已经包含点了，文件的具体格式可以打开参考一下
#         # self.mission.start_mission(
#         #     mission=[(20, 20, 5), (20, -20, 5), (-20, -20, 5), (-20, 20, 5)]
#         # )
  
#         waypoint_file = "./waypoint/waypoint1.txt"
#         try:
#             self.mission.start_mission_with_waypoint_file(waypoint_file)
#         except Exception as e:
#             self._logger.error(f"Failed to start mission from {waypoint_file}: {e}")
  


#         # 在这个地方 增加各种各样的定时器
#         self.provider.tracked_variables["packets"] = self.packets
#         self.provider.schedule_timer("", self.provider.current_time() + random.random())
#         self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)



#     def handle_timer(self, timer: str):
#         if timer == "energy_consumption":
#             self._schedule_energy_consumption()
#         elif timer == "charging_complete":
#             self._complete_charging()
#         ping = SimpleMessage(sender=SenderType.DRONE, content=self.packets)
        
#         self.provider.send_communication_command(
#             BroadcastMessageCommand(ping.to_json())
#         )

#         self.provider.schedule_timer("", self.provider.current_time() + random.random())


#     # 下面代码写的不好
#     def handle_packet(self, message: str):
#         message: SimpleMessage = SimpleMessage.from_json(message)
#         self._logger.debug(
#             #下面的先注释 看看有什么问题
#             #f"SimpleProtocolMobile received packet: {self.packets}, {message.sender}"
#             f"无人机收到{message.sender}包"
#         )

#         if message.sender == SenderType.GROUND_STATION:
#             self.packets = 0
#             self.provider.tracked_variables["packets"] = self.packets

#             if self.mission.is_reversed:
#                 reversed = not self.mission.is_reversed
#                 self.mission.set_reversed(reversed=reversed)

#         elif message.sender == SenderType.SENSOR:
#             self.packets += message.content
#             self.provider.tracked_variables["packets"] = self.packets
    

#     # 处理遥测数据
#     def handle_telemetry(self, telemetry: Telemetry):
#         # 将传入的遥测数据赋值给last_telemetry_message
#         self.last_telemetry_message = telemetry

#     def finish(self):
#         finish_statistics(self)


#     def _schedule_energy_consumption(self):
#         """每秒减少电量，低电量时触发充电"""
#         if not self.is_charging:
#             self.energy -= self.energy_consumption_rate
#             self._logger.info(f"Energy level: {self.energy}")

#             if self.energy <= self.low_energy_threshold:
#                 self._logger.info("Low energy! Returning to charging station.")
#                 self.go_to_nearest_charge_station()
#             else:
#                 # 继续调度下一次能量消耗
#                 self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)


#     def go_to_nearest_charge_station(self):
#         """前往最近的充电站"""
#         self.is_charging = True
#         self._logger.info("Navigating to charging station...")
#         self.provider.send_mobility_command(SetSpeedMobilityCommand(0))  # 停止移动
#         self.provider.schedule_timer("charging_complete", self.provider.current_time() + 5)


#     def _complete_charging(self):
#         """充电完成，恢复满电"""
#         self.energy = 100
#         self.is_charging = False
#         self._logger.info("Charging complete. Battery is now full.")
#         # 重新启动能量消耗
#         self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)



import logging
import math
import random
import time
from gradysim.protocol.plugin.mission_mobility import (
    LoopMission,
    MissionMobilityPlugin,
    MissionMobilityConfiguration,
)
from gradysim.protocol.plugin.statistics import create_statistics, finish_statistics
from gradysim.protocol.messages.communication import BroadcastMessageCommand


from gradysim.protocol.messages.telemetry import Telemetry
from gradysim.protocol.interface import IProtocol
from message import SimpleMessage, SenderType
from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand, SetSpeedMobilityCommand



class SimpleProtocolMobile(IProtocol):

    def __init__(self):

        #以下是无人机自带的收集数据包相关内容
        self.packets: int = 0

        #以下是无人机自带的遥感信息
        self.last_telemetry_message: Telemetry

        #以下是无人机日志
        self._logger = logging.getLogger()
        self._logger.propagate = False

        #以下是无人机电量相关内容
        self.energy = 10000  # 初始电池电量
        self.low_energy_threshold = 20  # 低电量阈值
        self.energy_consumption_rate = 2  # 每秒消耗3点电量
        self.is_charging = False  # 是否正在充电

        #以下是无人机存储数据的地方
        self.data_log_file = "./result/data_log1.txt"
        with open(self.data_log_file, "w") as f:
            f.write("UAV Data Log:\n")

        #以下是无人机写数据的时间
        self.last_written_data = None
        self.last_write_time = 0  # 记录上次写入的时间

        #以下是无人机统计通信节点的部分
        self.successful_nodes = set()  # 记录成功通信的节点
        self.total_waypoints = 0  # 总节点数（从文件读取）

        #以下是无人机实际总飞行距离
        self.last_telemetry_position = None
        self.total_flight_distance = 0.0

        #以下是有关无人机收集数据时传输延迟的部分
        self.total_communication_latency = 0.0
        self.communitaion_events_count = 0

    def save_sensor_data(self):
        """ 只有当数据发生变化，并且上次写入超过 1 秒，才写入日志 """

        current_time = time.time()

        if self.packets != self.last_written_data and current_time - self.last_write_time > 0.5:
            with open(self.data_log_file, "a") as f:
                f.write(f"Total Data from Sensors: {self.packets}\n")
            self.last_written_data = self.packets
            self.last_write_time = current_time  # 更新时间戳
        

    def initialize(self):
        self._logger.debug("初始化无人机节点")
        print(f"[DEBUG] UAV 初始电量: {self.energy}")

        # create_statistics(self)  #统计数据函数

        self.mission: MissionMobilityPlugin= MissionMobilityPlugin(
            self, MissionMobilityConfiguration(loop_mission=LoopMission.RESTART)
        )

        """
        如果是刚接触这个项目的人，可以用添加这种简单的飞行点来熟悉，下面是用文件，文件里面已经包含点了，文件的具体格式可以打开参考一下
        self.mission.start_mission(mission=[(20, 20, 5), (20, -20, 5), (-20, -20, 5), (-20, 20, 5)])
        """

        """
         这个地方的waypoint路线点，就是后期BQ算法生成的最优路径，拿过来，放在这个地方跑一下。
         跑出来的就是最优路径
         注意区分刚刚和main函数里面的不同，main函数是点路径，这个地方是飞行路径
        """

        waypoint_file = "./waypoint/tsp_100_nodes_file1.txt"
        try:
            self.mission.start_mission_with_waypoint_file(waypoint_file)
        except Exception as e:
            self._logger.error(f"Failed to start mission from {waypoint_file}: {e}")

        """动态统计一共有多少个节点"""
        try:
            with open(waypoint_file, 'r') as f:
                self.total_waypoints = sum(1 for _ in f)
        except Exception as e:
            self._logger.error(f"Failed to read waypoint file: {e}")
  

        '''在这个地方 增加各种各样的定时器'''
        self.provider.tracked_variables["packets"] = self.packets
        self.provider.schedule_timer("", self.provider.current_time() + random.random())
        self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)



    def handle_timer(self, timer: str):
        if timer == "energy_consumption":
            self._schedule_energy_consumption()
        elif timer == "charging_complete":
            self._complete_charging()
        ping = SimpleMessage(sender=SenderType.DRONE, content=self.packets,id = self.provider.get_id(),timestamp=self.provider.current_time())

        self.provider.send_communication_command(
            BroadcastMessageCommand(ping.to_json())
        )

        self.provider.schedule_timer("", self.provider.current_time() + random.random())


    # 下面代码写的不好
    def handle_packet(self, message: str):
        message: SimpleMessage = SimpleMessage.from_json(message)
        self._logger.debug(
            #下面的先注释 看看有什么问题
            #f"SimpleProtocolMobile received packet: {self.packets}, {message.sender}"
            f"无人机收到{message.sender}包"
        )


        if message.sender == SenderType.GROUND_STATION:
            self.packets = 0
            self.provider.tracked_variables["packets"] = self.packets

            if self.mission.is_reversed:
                reversed = not self.mission.is_reversed
                self.mission.set_reversed(reversed=reversed)

        elif message.sender == SenderType.SENSOR:
            self.packets += message.content
            self.provider.tracked_variables["packets"] = self.packets
            self.save_sensor_data()
            self.successful_nodes.add(message.id)  # message.content可以换成唯一ID（如sensor编号）这一行也是新加的
            latency = self.provider.current_time() - message.timestamp
            self.total_communication_latency += latency
            self.communitaion_events_count += 1

    # 处理遥测数据
    def handle_telemetry(self, telemetry: Telemetry):
        # 将传入的遥测数据赋值给last_telemetry_message
        self.last_telemetry_message = telemetry

        # 获取当前的 (x, y, z) 元组
        current_x, current_y, current_z = telemetry.current_position

        # 检查是否是第一次接收遥测数据
        if self.last_telemetry_position is not None:
            # 从存储的上一个位置元组中解包
            prev_x, prev_y, prev_z = self.last_telemetry_position

            distance = math.sqrt(
                (current_x - prev_x) ** 2 +
                (current_y - prev_y) ** 2 +
                (current_z - prev_z) ** 2
            )
            self.total_flight_distance += distance

        # 更新上一个位置为当前的 (x, y, z) 元组
        self.last_telemetry_position = (current_x, current_y, current_z)

    def finish(self):
        # finish_statistics(self)  结束统计数据
        with open(self.data_log_file, "a") as f:
            """下面这两行是统计一共收集到了多少数据"""
            f.write(f"Total Data from Sensors: {self.packets}\n")  # 强制写入当前数据
            f.write(f"\nFinal Total Data from Sensors: {self.packets}\n")

            """下面这9行是新需求1的完成。统计一次任务中数据收集完整率（有多少物联网节点的数据被收集到了）"""
            success_count = len(self.successful_nodes)
            fail_count = self.total_waypoints - success_count
            success_rate = success_count / self.total_waypoints if self.total_waypoints > 0 else 0
            fail_rate = fail_count / self.total_waypoints if self.total_waypoints > 0 else 0
            f.write(f"\nTotal Waypoints (Nodes): {self.total_waypoints}\n")
            f.write(f"Successful Communications: {success_count}\n")
            f.write(f"Failed Communications: {fail_count}\n")
            f.write(f"Success Rate: {success_rate:.2%}\n")
            f.write(f"Failure Rate: {fail_rate:.2%}\n")
            total_energy_consumed = 10000 - self.energy
            efficiency = self.packets / total_energy_consumed if total_energy_consumed > 0 else 0
            f.write(f"\nTotal Energy Consumed: {total_energy_consumed}\n")
            f.write(f"Efficiency (Data per Unit Energy): {efficiency:.4f} packets/unit_energy\n")

            #总飞行距离
            f.write(f"\n总飞行距离: {self.total_flight_distance}\n")

            #总通信时延
            f.write(f"\n总通信时延: {self.total_communication_latency}\n")

            #平均通信时延
            f.write(f"\n平均通信时延: {self.total_communication_latency / self.communitaion_events_count}\n")

    def _schedule_energy_consumption(self):
        """每秒减少电量，低电量时触发充电"""
        if not self.is_charging:
            self.energy -= self.energy_consumption_rate                              #这个地方为了保持满电，我先将减号改成加号
            self._logger.info(f"Energy level: {self.energy}")

            if self.energy <= self.low_energy_threshold:
                self._logger.info("Low energy! Returning to charging station.")
                self.go_to_nearest_charge_station()
            else:
                # 继续调度下一次能量消耗
                self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)


    def go_to_nearest_charge_station(self):
        """前往最近的充电站"""
        self.is_charging = True
        self._logger.info("Navigating to charging station...")
        self.provider.send_mobility_command(SetSpeedMobilityCommand(0))  # 停止移动
        self.provider.schedule_timer("charging_complete", self.provider.current_time() + 5)


    def _complete_charging(self):
        """充电完成，恢复满电"""
        self.energy = 100
        self.is_charging = False
        self._logger.info("Charging complete. Battery is now full.")
        # 重新启动能量消耗
        self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)


