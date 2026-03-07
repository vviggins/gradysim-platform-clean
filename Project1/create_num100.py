# import random
#
# # 生成100个三维坐标点，x,y范围是0-100，z=0，格式为"x,y,z"
# points = []
# for _ in range(100):
#     x = round(random.uniform(0, 100), 2)
#     y = round(random.uniform(0, 100), 2)
#     z = 0
#     points.append(f"{x},{y},{z}")
#
# # 保存到txt文件
# file_path = './waypoint/tsp_100_nodes_file1.txt'
# with open(file_path, 'w') as f:
#     for point in points:
#         f.write(point + '\n')
#
# file_path

import os

def generate_s_path(x_range=100, y_range=100, step=10):
    path = []
    for y_index, y in enumerate(range(0, y_range, step)):
        if y_index % 2 == 0:
            # 左到右
            for x in range(0, x_range, step):
                path.append((x, y, 0))
        else:
            # 右到左
            for x in reversed(range(0, x_range, step)):
                path.append((x, y, 0))
    return path

def save_path_to_txt(path, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        for x, y, z in path:
            f.write(f"{x},{y},{z}\n")

# 主程序入口
if __name__ == "__main__":
    path = generate_s_path(x_range=100, y_range=100, step=10)  # 会生成11*10=110个点
    trimmed_path = path[:100]  # 截取前100个点（你指定的）
    file_path = './waypoint/tsp_100_nodes_file1.txt'
    save_path_to_txt(trimmed_path, file_path)
    print(f"路径已保存到: {file_path}")
