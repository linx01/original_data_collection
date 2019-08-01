# -*-coding:utf-8 -*-
import requests
import base64
import json
import ctypes

"""
验证码识别
"""


class Ocr(object):

    def __init__(self):
        self._server_url = 'http://103.71.238.242:8181/'
        self._server_url = 'http://119.23.212.206:8189/'
        # self._server_url = 'http://127.0.0.1:8080/'

    def discern(self, code):
        """
        :param code: 二进制验证码
        :return:
        """
        try:
            request = {
                'code': base64.b64encode(code)
            }
            res = requests.post(self._server_url + 'ocr', data=request, timeout=30)
            if res.status_code != 200:
                return {'code': res.status_code, 'error': '访问页面超时'}

            array = json.loads(res.content)
            if array.get('code', 100) == 0 and array.get('data', []).get('code', None) is not None:
                return {'code': 0, 'result': array.get('data', []).get('code', None)}
            return {'code': res.status_code, 'error': '识别失败'}
        except BaseException as e:
            return e


ocr = Ocr()

if __name__ == '__main__':
    # 调用实例
    response = requests.get('http://webo.hnjuchu.com/user/verify_code.html')
    # print(response.content)
    print(ocr.discern(response.content))
    # dll = ctypes.windll.LoadLibrary(r"H:\python\dev_platform\public\ocr.dll")
    # dll.init()
    # print(len(response.content))
    # print(dll.ocr(response.content, len(response.content)))
    pass
