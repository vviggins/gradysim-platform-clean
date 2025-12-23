# GA_refactored.py
import random
import math
import time
import numpy as np

class GA(object):
    def __init__(self, num_city, iteration, data, num_total=50, ga_choose_ratio=0.2, mutate_ratio=0.2):
        self.num_city = num_city
        self.num_total = num_total  # 种群数量
        self.iteration = iteration
        self.location = data
        self.ga_choose_ratio = ga_choose_ratio
        self.mutate_ratio = mutate_ratio
        
        # fruits中存每一个个体是下标的list
        self.fruits = self.random_init(self.num_total, self.num_city)
        self.dis_mat = self.compute_dis_mat(self.num_city, self.location)
        
        # 存储每个iteration的结果
        self.iter_y = []

    def random_init(self, num_total, num_city):
        tmp = list(range(num_city))
        result = []
        for i in range(num_total):
            random.shuffle(tmp)
            result.append(tmp.copy())
        return result

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

    def compute_adp(self, fruits):
        adp = [1.0 / self.compute_pathlen(fruit, self.dis_mat) for fruit in fruits]
        return np.array(adp)

    def ga_cross(self, x, y):
        len_ = len(x)
        assert len(x) == len(y)
        path_list = list(range(len_))
        order = list(random.sample(path_list, 2))
        order.sort()
        start, end = order

        tmp = x[start:end]
        x_conflict_index = [y.index(sub) for sub in tmp if not (start <= y.index(sub) < end)]
        y_conflict_index = [x.index(sub) for sub in y[start:end] if not (start <= x.index(sub) < end)]

        assert len(x_conflict_index) == len(y_conflict_index)

        tmp_swap = x[start:end].copy()
        x[start:end] = y[start:end]
        y[start:end] = tmp_swap

        for i in range(len(x_conflict_index)):
            idx1 = x_conflict_index[i]
            idx2 = y_conflict_index[i]
            y[idx1], x[idx2] = x[idx2], y[idx1]

        assert len(set(x)) == len_ and len(set(y)) == len_
        return list(x), list(y)

    def ga_parent(self, scores, ga_choose_ratio):
        sort_index = np.argsort(-scores)
        select_num = int(ga_choose_ratio * len(sort_index))
        parents_index = sort_index[:select_num]
        parents = [self.fruits[i] for i in parents_index]
        parents_score = [scores[i] for i in parents_index]
        return parents, parents_score

    def ga_choose(self, genes_score, genes_choose):
        sum_score = sum(genes_score)
        score_ratio = [sub / sum_score for sub in genes_score]
        
        # 使用 numpy 的 choice 更高效
        chosen_indices = np.random.choice(len(genes_choose), 2, p=score_ratio)
        return list(genes_choose[chosen_indices[0]]), list(genes_choose[chosen_indices[1]])

    def ga_mutate(self, gene):
        path_list = list(range(len(gene)))
        order = list(random.sample(path_list, 2))
        start, end = min(order), max(order)
        gene[start:end] = gene[start:end][::-1]
        return list(gene)

    def ga(self):
        scores = self.compute_adp(self.fruits)
        parents, parents_score = self.ga_parent(scores, self.ga_choose_ratio)
        
        tmp_best_one = parents[0]
        tmp_best_score = parents_score[0]
        
        fruits = parents.copy()
        while len(fruits) < self.num_total:
            gene_x, gene_y = self.ga_choose(parents_score, parents)
            gene_x_new, gene_y_new = self.ga_cross(gene_x, gene_y)

            if np.random.rand() < self.mutate_ratio:
                gene_x_new = self.ga_mutate(gene_x_new)
            if np.random.rand() < self.mutate_ratio:
                gene_y_new = self.ga_mutate(gene_y_new)
            
            fruits.append(gene_x_new)
            if len(fruits) < self.num_total:
                fruits.append(gene_y_new)

        self.fruits = fruits
        return tmp_best_one, tmp_best_score

    def run(self):
        start_time = time.time()
        
        best_list = None
        best_score = -math.inf

        for i in range(self.iteration):
            tmp_best_one, tmp_best_score = self.ga()
            self.iter_y.append(1. / tmp_best_score)
            if tmp_best_score > best_score:
                best_score = tmp_best_score
                best_list = tmp_best_one
            # print(f"GA Iteration {i+1}/{self.iteration}, Best Length: {1./best_score:.2f}")

        end_time = time.time()
        
        best_length = 1. / best_score
        execution_time = end_time - start_time
        
        return best_length, execution_time

# 这是一个测试用的主程序入口
if __name__ == '__main__':
    # 生成随机测试数据
    num_cities = 50
    test_data = np.random.rand(num_cities, 2) * 100

    # 初始化并运行算法
    ga_solver = GA(num_city=num_cities, iteration=200, data=test_data)
    best_len, run_time = ga_solver.run()

    print(f"GA Final Best Path Length: {best_len}")
    print(f"GA Execution Time: {run_time:.4f} seconds")