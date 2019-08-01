# -*- coding:utf-8 -*-
# @Time    : 2019/7/7 18:53
# @Author  : Linx
# @File    : configs.py
# @Software: PyCharm
# @Contact : 410559855@qq.com

from urls import *
from Structure_public import *
from platformBase.yileCommunity import Handle_YiLe
from platformBase.ninefiveCommunity import Handle_NineFive

configers = {}

# 运行配置：目标域名/进程数/目标函数/执行函数/框架名称
configers.update(
    dict(
        urls=urls_filter,
        process_number=5,
        target=filter_,
        execute=handle_process,
        structure_name='ninefivecommunity',
    )
)

# 框架:新框架此处添加
configers.update(
    dict(
        yilecommunity=Handle_YiLe,
        ninefivecommunity=Handle_NineFive,
    )
)



