# -*- coding:utf-8 -*-
# @Time    : 2019/7/7 19:15
# @Author  : Linx
# @File    : run.py
# @Software: PyCharm
# @Contact : 410559855@qq.com

from configs import configers


function = configers.get('execute', '')
target = configers.get('target', '')
process_number = configers.get('process_number', 1)
urls = configers.get('urls', [])
structure = configers.get(configers.get('structure_name', ''), '')


if __name__ == '__main__':
    function(urls,process_number,target,structure)