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
        self.energy = 100  # 初始电池电量
        self.low_energy_threshold = 20  # 低电量阈值
        self.energy_consumption_rate = 3  # 每秒消耗3点电量
        self.is_charging = False  # 是否正在充电

        #以下是无人机存储数据的地方
        self.data_log_file = "./result/data_log1.txt"
        with open(self.data_log_file, "w") as f:
            f.write("UAV Data Log:\n")

        #以下是无人机写数据的时间
        self.last_written_data = None
        self.last_write_time = 0  # 记录上次写入的时间
    
    def save_sensor_data(self):
        """ 只有当数据发生变化，并且上次写入超过 1 秒，才写入日志 """

        current_time = time.time()

        if self.packets != self.last_written_data and current_time - self.last_write_time > 1:
            with open(self.data_log_file, "a") as f:
                f.write(f"Total Data from Sensors: {self.packets}\n")
            self.last_written_data = self.packets
            self.last_write_time = current_time  # 更新时间戳
        

    def initialize(self):
        self._logger.debug("初始化无人机节点")
        print(f"[DEBUG] UAV 初始电量: {self.energy}")



        create_statistics(self)  #统计数据函数

        self.mission: MissionMobilityPlugin= MissionMobilityPlugin(
            self, MissionMobilityConfiguration(loop_mission=LoopMission.RESTART)
        )


        # 如果是刚接触这个项目的人，可以用添加这种简单的飞行点来熟悉，下面是用文件，文件里面已经包含点了，文件的具体格式可以打开参考一下
        # self.mission.start_mission(
        #     mission=[(20, 20, 5), (20, -20, 5), (-20, -20, 5), (-20, 20, 5)]
        # )
  
        waypoint_file = "./waypoint/waypoint1.txt"
        try:
            self.mission.start_mission_with_waypoint_file(waypoint_file)
        except Exception as e:
            self._logger.error(f"Failed to start mission from {waypoint_file}: {e}")
  


        # 在这个地方 增加各种各样的定时器
        self.provider.tracked_variables["packets"] = self.packets
        self.provider.schedule_timer("", self.provider.current_time() + random.random())
        self.provider.schedule_timer("energy_consumption", self.provider.current_time() + 1)



    def handle_timer(self, timer: str):
        if timer == "energy_consumption":
            self._schedule_energy_consumption()
        elif timer == "charging_complete":
            self._complete_charging()
        ping = SimpleMessage(sender=SenderType.DRONE, content=self.packets)
        

        



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
    

    # 处理遥测数据
    def handle_telemetry(self, telemetry: Telemetry):
        # 将传入的遥测数据赋值给last_telemetry_message
        self.last_telemetry_message = telemetry

    def finish(self):
        finish_statistics(self)
        with open(self.data_log_file, "a") as f:
            f.write(f"Total Data from Sensors: {self.packets}\n")  # 强制写入当前数据
            f.write(f"\nFinal Total Data from Sensors: {self.packets}\n")


    def _schedule_energy_consumption(self):
        """每秒减少电量，低电量时触发充电"""
        if not self.is_charging:
            self.energy -= self.energy_consumption_rate
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