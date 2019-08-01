# -*- coding:utf-8 -*-
# @Time    : 2019/7/7 10:32
# @Author  : Linx
# @File    : mysqlhelper.py
# @Software: PyCharm
# @Contact : 410559855@qq.com

from multiprocessing import Process, Manager


def register_(index, last, l, pid, length, urls, structure):
    structure.register(index, last, l, pid, length, urls)


def filter_(index, last, l, pid, length, urls, structure):
    structure.filter(index, last, l, pid, length, urls)


def collection_(index, last, l, pid, length, urls, structure):
    structure.collection(index, last, l, pid, length, urls)


def handle_process(urls, count, function, structure):
    with Manager() as manager:
        # 创建进程间通信共享列表
        l = manager.list()
        # 总数量
        length = len(urls)
        # 步长
        lens = int(length / count)
        # 下标
        global index_
        index_ = [x for x in range(0, length - 1, lens)]
        processes = []
        for index in index_:
            # 判断是否是最后一个进程,如果是则取全部,避免无法整除的情况
            if index == index_[-1]:
                last = None
            else:
                last = index + lens
            # 取进程号
            pid = index_.index(index) + 1
            print(index, last, pid)
            p = Process(target=function, args=(index, last, l, pid, length, urls, structure))
            processes.append(p)
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        print('process - all - over -')

        # 遍历进程间共享列表
        for elem in l:
            print(elem)
