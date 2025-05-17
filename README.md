# GrADyS-SIM NextGen
This repository contains the source code for the GrADyS-SIM NextGen simulation framework. Visit 
https://project-gradys.github.io/gradys-sim-nextgen/ to view the project's documentation, usage tutorials
and installation instructions.

## Installation
> pip install gradysim
1. （不熟悉)如果你是刚接触这个项目的新手，你可以先创建一个虚拟环境，然后再虚拟环境里面pip install gradysim 这么做的目的是你刚开始先熟悉一下这个项目能做
   （**1. 数据收集**，**2.多无人机跟随一个无人机**）

   
2. （熟悉）如果你已经很熟悉这个项目了，已经知道了这个项目的大部分架构，可以对底层框架进行修改，想要对底层框架进行修改来增加功能时
  **就不能pip install gradysim了**
   原因是 当你 **pip install gradysim**的时候，你每个文件刚开始导包，导的都是原作者写好的gradysim包
   
   2.1  如果你想根据底层框架增添新的功能，建议您新建一个环境，然后不装包，直接进行测试，看看能否运行showcases中的例子，如果可以，那么您能继续使用。
   
   2.2  如果发现不装包的情况下，报错提示你装包，**恭喜你**，我目前也没解决这个问题


# 入门
这个系统刚开始的时候，给了三个例子，在showcases文件夹下面，如果你安装了 pip install gradysim的话，你只能修改一些基本的数据（在main.py中），比如增加多少无人机，增加多少传感器
## 入门能使用的功能
### 1. 简单的数据收集
在showcases文件夹下面的simple文件夹，就是一个简单的无人机收集数据的例子，由于该项目是基于事件驱动的项目，无人机和传感器之间的数据收集（无人机问传感器要数据）是通过无人机和传感器之间的通信来实现的。
无人机一直广播（广播发给所有的传感器），当无人机和传感器 $n_i$ 在通信范围里面的时候

# 高级
## 目前高级能实现的功能
1. 数据收集完整率 ：关注的是任务的完成度——即在任务周期结束时，有多少比例的目标物联网设备的数据被完整收集了。它衡量的是“**是否完成了对每个节点的服务**”

2. 系统吞吐量 (平均/总和)：关注的是数据的传输效率——即单位时间内从无人机成功传输到基站（BS）的数据总量。它衡量的是“**数据流向中心节点的速率和效率**”。

3. 无人机能量利用效率：关注的是无人机的能量利用情况——即每架无人机收集的总数据量与其总能耗的平均比率，量化了“**每单位能耗收集的数据量**”

4. **数据收集延迟**：
5. **批量导点**，比如你有100个无人机，或者传感器，你可以通过文件的形式，加入进去，原来的项目是一行一行增加，
   -  优势：整理好的txt文件直接传进去就好了
7. 调整整个模拟情况的**通信失败率**，以造成通信失败，模拟现实的真实场景
   - 优势：论文写作
9. 找到每个无人机，以及每个传感器的**id**
    - 优势：可以判断是哪个无人机 -> 从哪个传感器，收集到的数据（进一步可以模拟，是否对该点进行服务过)
11. **充电**：当无人机电量少于**energy_threshold**的时候，无人机自动飞往充电站，进行充电
    - 优势：充电

# 模块说明
# 1. main.py
初始化模拟器，构建通信、计时、移动、可视化等处理模块。

添加地面站、无人机、传感器节点，并设置其初始坐标。

启动仿真流程。

# 2. message.py
定义统一的消息格式 SimpleMessage，支持序列化与反序列化，用于无人机、地面站、传感器之间的数据传递。

```python
class SimpleMessage:
    sender: SenderType
    content: int
```

# 3. simple_ground.py（类名：SimpleProtocolGround）
接收来自无人机的消息，累加内容并广播回复。

跟踪统计信息 packets。

# 4. simple_mobile.py（类名：SimpleProtocolMobile）
执行循环飞行任务。

周期性向地面站发送数据。

接收来自地面站与传感器的消息并响应。

# 5. simple_sensor.py（类名：SimpleProtocolSensor）
周期性产生数据。

接收无人机请求后回应数据并清零缓存。
