from enum import Enum
import json

'''这个是发送者的种类，三种，无人机，传感器，地面站。
'''
class SenderType(int, Enum):
    DRONE = 0
    SENSOR = 1
    GROUND_STATION = 2


class SimpleMessage:
    sender: SenderType
    content: int
    id: int

    def __init__(self, sender: SenderType, content: int,id: int) -> None:
        self.sender = sender
        self.content = content
        self.id = id

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)