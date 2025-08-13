import sys

print("模块搜索顺序（sys.path）：\n")
for i, p in enumerate(sys.path):
    print(f"{i+1}. {p}")