# SA_refactored.py
import random
import math
import time
import numpy as np

class SA(object):
    def __init__(self, num_city, data, T0=2000, Tend=1e-3, rate=0.94, size=100):
        self.num_city = num_city
        self.location = data
        self.T0 = T0
        self.Tend = Tend
        self.rate = rate
        self.size = size # 每个温度下的迭代次数
        
        self.fire = self.random_init(num_city)
        self.dis_mat = self.compute_dis_mat(num_city, data)
        
        self.iter_y = []

    def random_init(self, num_city):
        tmp = list(range(num_city))
        random.shuffle(tmp)
        return tmp

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

    def get_new_fire(self, fire):
        t = list(range(len(fire)))
        a, b = np.random.choice(t, 2, replace=False)
        x, y = min(a, b), max(a, b)
        # 片段逆转
        return fire[:x] + fire[x:y][::-1] + fire[y:]

    def eval_fire(self, raw, get, temp):
        len1 = self.compute_pathlen(raw, self.dis_mat)
        len2 = self.compute_pathlen(get, self.dis_mat)
        dc = len2 - len1
        if dc < 0:
            return get, len2
        else:
            p = np.exp(-dc / temp)
            if np.random.rand() <= p:
                return get, len2
            else:
                return raw, len1

    def sa(self):
        current_path = self.fire
        current_length = self.compute_pathlen(current_path, self.dis_mat)
        
        best_path = current_path
        best_length = current_length
        
        T = self.T0
        while T > self.Tend:
            for _ in range(self.size):
                new_path = self.get_new_fire(current_path.copy())
                current_path, current_length = self.eval_fire(current_path, new_path, T)
                
                if current_length < best_length:
                    best_length = current_length
                    best_path = current_path
            
            T *= self.rate
            self.iter_y.append(best_length)
            # print(f"Temperature: {T:.2f}, Best Length: {best_length:.2f}")

        return best_length, best_path

    def run(self):
        start_time = time.time()
        
        best_length, best_path = self.sa()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return best_length, execution_time

# 这是一个测试用的主程序入口
if __name__ == '__main__':
    # 生成随机测试数据
    num_cities = 50
    test_data = np.random.rand(num_cities, 2) * 100
    
    # 初始化并运行算法
    sa_solver = SA(num_city=num_cities, data=test_data)
    best_len, run_time = sa_solver.run()

    print(f"SA Final Best Path Length: {best_len}")
    print(f"SA Execution Time: {run_time:.4f} seconds")