# ACO_refactored.py
import random
import math
import time
import numpy as np

class ACO(object):
    def __init__(self, num_city, data, iter_max=500, m=30, alpha=1, beta=5, rho=0.1, Q=1):
        self.num_city = num_city
        self.location = data
        self.iter_max = iter_max
        self.m = m  # 蚂蚁数量
        self.alpha = alpha  # 信息素重要程度因子
        self.beta = beta  # 启发函数重要因子
        self.rho = rho  # 信息素挥发因子
        self.Q = Q  # 常量系数
        
        self.dis_mat = self.compute_dis_mat(num_city, self.location)
        self.Tau = np.ones((num_city, num_city))  # 信息素矩阵
        self.Eta = 1.0 / self.dis_mat  # 启发式函数, 避免除零
        np.fill_diagonal(self.Eta, 0) # 对角线填充为0
        
        self.Table = [[0 for _ in range(num_city)] for _ in range(self.m)]  # 生成的蚁群
        
        self.iter_y = []

    def rand_choose(self, p):
        x = np.random.rand()
        for i, t in enumerate(p):
            x -= t
            if x <= 0:
                break
        return i

    def get_ants(self):
        for i in range(self.m):
            start = np.random.randint(self.num_city)
            self.Table[i][0] = start
            unvisit = list(range(self.num_city))
            unvisit.remove(start)
            
            current = start
            for j in range(1, self.num_city):
                P = []
                for v in unvisit:
                    P.append(self.Tau[current][v] ** self.alpha * self.Eta[current][v] ** self.beta)
                
                P_sum = sum(P)
                if P_sum == 0: # 防止所有路径概率为0
                    # 如果发生这种情况，随机选择一个未访问的城市
                    next_city_index = np.random.randint(len(unvisit))
                else:
                    P = [x / P_sum for x in P]
                    next_city_index = self.rand_choose(P)

                current = unvisit[next_city_index]
                self.Table[i][j] = current
                unvisit.remove(current)

    def compute_dis_mat(self, num_city, location):
        dis_mat = np.zeros((num_city, num_city))
        for i in range(num_city):
            for j in range(num_city):
                if i == j:
                    dis_mat[i][j] = np.inf
                    continue
                a = location[i]
                b = location[j]
                tmp = np.sqrt(sum([(x[0] - x[1]) ** 2 for x in zip(a, b)]))
                dis_mat[i][j] = tmp
        return dis_mat

    def compute_pathlen(self, path, dis_mat):
        a = path[0]
        b = path[-1]
        result = dis_mat[a][b]
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            result += dis_mat[a][b]
        return result

    def compute_paths(self, paths):
        return [self.compute_pathlen(one, self.dis_mat) for one in paths]

    def update_Tau(self):
        delta_tau = np.zeros((self.num_city, self.num_city))
        paths_len = self.compute_paths(self.Table)
        
        for i in range(self.m):
            for j in range(self.num_city - 1):
                a = self.Table[i][j]
                b = self.Table[i][j + 1]
                delta_tau[a][b] += self.Q / paths_len[i]
            
            # 回到起点
            a = self.Table[i][-1]
            b = self.Table[i][0]
            delta_tau[a][b] += self.Q / paths_len[i]
        
        self.Tau = (1 - self.rho) * self.Tau + delta_tau

    def aco(self):
        best_length = math.inf
        best_path = None
        
        for cnt in range(self.iter_max):
            self.get_ants()
            paths_len = self.compute_paths(self.Table)
            
            tmp_length = min(paths_len)
            if tmp_length < best_length:
                best_length = tmp_length
                best_path = self.Table[paths_len.index(tmp_length)]
            
            self.update_Tau()
            self.iter_y.append(best_length)
            # print(f"ACO Iteration {cnt+1}/{self.iter_max}, Best Length: {best_length:.2f}")

        return best_length, best_path

    def run(self):
        start_time = time.time()
        
        best_length, best_path = self.aco()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return best_length, execution_time

# 这是一个测试用的主程序入口
if __name__ == '__main__':
    # 生成随机测试数据
    num_cities = 50
    test_data = np.random.rand(num_cities, 2) * 100

    # 初始化并运行算法
    aco_solver = ACO(num_city=num_cities, data=test_data)
    best_len, run_time = aco_solver.run()

    print(f"ACO Final Best Path Length: {best_len}")
    print(f"ACO Execution Time: {run_time:.4f} seconds")