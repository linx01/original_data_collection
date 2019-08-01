# -*- coding:utf-8 -*-
# @Time    : 2019/7/7 10:32
# @Author  : Linx
# @File    : mysqlhelper.py
# @Software: PyCharm
# @Contact : 410559855@qq.com

import pymysql
from env import env

class MysqlHelper(object):
    def __init__(self):
        self.connection = pymysql.connect(
        host=env('mysql','host','127.0.0.1'),
        user=env('mysql','user','root'),
        password=env('mysql','password', '123456'),
        db=env('mysql','db', 'test'),
        port=int(env('mysql','port', 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        write_timeout=int(env('mysql','write_timeout', 60)),
        read_timeout=int(env('mysql','read_timeout', 30))
        )
    # 链接
    def handle(self):
        return self.connection
    # 游标
    def cursor(self):
        return self.connection.cursor()
    # 提交
    def commit(self):
        self.connection.commit()
    # 回滚
    def rollback(self):
        self.connection.rollback()
    # 断开链接
    def close(self):
        self.connection.close()

    # 查找记录
    def search(self, href, pid):
        table_name = 'yilecommunity{}'.format(pid)
        sql = """
        SELECT * FROM `{0}` WHERE `goods_link`="{1}"
        """.format(table_name, href)
        cursor = self.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    # 插入数据
    def add(self, info, pid):
        try:
            table_name = 'yilecommunity{}'.format(pid)
            sql = """
            INSERT INTO `{13}` (platform_name,goods_title,goods_price,goods_min,goods_max,goods_id,goods_type,goods_link,username,password,customerservice,notice,platform_url) VALUES("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}")
            """.format(
                info['platformName'],
                info['goodsTitle'],
                info['goodsPrice'],
                info['goods_min'],
                info['goods_max'],
                info['goods_id'],
                info['goods_type'],
                info['href'],
                info['username'],
                info['password'],
                info['customerservice'],
                info['notice'],
                info['platform_url'],
                table_name
            )

            cursor = self.cursor()
            res = cursor.execute(sql)
            self.commit()
            return res
        except Exception as e:
            self.rollback()
            return 0


mysqlhelper = MysqlHelper()

if __name__ == '__main__':
    print(mysqlhelper.search('http://www.baidu.com'))
    # info = {
    #     'platformName': 'abcd',
    #     'goodsTitle': 'dddd',
    #     'goodsPrice': 'sddd',
    #     'goods_min': 10,
    #     'goods_max': 1000,
    #     'goods_id': 12354,
    #     'goods_type': 1254,
    #     'href': 'www.baidu.com',
    #     'username':'linx01',
    #     'password': '123456',
    #     'customerservice': 'sdd',
    #     'notice': 'sdd',
    #     'platform_url': 'dddd'
    # }
    # print(mysqlhelper.add(info))