# coding=utf-8
import json
import random
import re
import time
from multiprocessing import Lock

import requests
from lxml import etree

from Ocrs import ocr
from mongodbhelper import mongohelper


class Platforminfo_NineFive(object):

    def filter(self):
        try:
            res = requests.get(url=self._url, headers=self._header, verify=False)
        except Exception as e:
            return {'code': 404, 'response': '{}无响应！原因:{}'.format(self._url, e)}

        if 'Domain Error' in res.text or 'failed' in res.text:
            return {'code': res.status_code, 'response': '域名{}无法访问!'.format(self._url) + res.text[:100]}
        elif res.status_code != 200:
            return {'code': res.status_code, 'response': '域名{}无法访问!'.format(self._url) + res.text[:100]}
        elif '该域名尚未搭建,可以使用!' in res.text:
            return {'code': res.status_code, 'response': '域名{}未搭建!'.format(self._url) + res.text[:100]}
        elif res.text.startswith('{'):
            res_ = json.loads(res.text.encode('utf-8'))
            return {'code': res.status_code,
                    'response': '域名{}无法访问，原因：{}'.format(self._url, res_['info']) + res.text[:100]}
        elif '页面跳转中' in res.text:
            result = re.findall(r"http:\/\/(.*)\/index\.php", self._url)
            self._header['Cookie'] = 'domain_jump={}; okdomain_jump={}'.format(result[0], result[0])
            self._header['Referer'] = self._url
            # 重定向访问
            res__ = requests.get(url=self._url + '?m=Home&c=DomainJump&a=index', headers=self._header, verify=False)
            if res__.text.startswith('{'):
                res_ = json.loads(res__.text.encode('utf-8'))
                if '站点已被' in res_['info'] or '网站装修中，请稍后' in res_['info'] or '系统已停止该站点的访问' in res_['info']:
                    return {'code': res__.status_code, 'response': '域名{}已由于{}无法访问!'.format(self._url, res_['info'])}
                else:
                    return {'code': 0, 'response': '域名{}可以访问!'.format(self._url) + str(res_)}
            else:
                content = etree.HTML(res__.text)
                try:
                    new_url = content.xpath(r"//a[@class='okDomain']/@href")[0]
                except:
                    if 'Domain Error' in res__.text or 'failed' in res__.text:
                        return {'code': res.status_code, 'response': '域名{}无法访问!'.format(self._url) + res__.text[:100]}
                    return {'code': 0, 'response': '域名{}经过跳转可以访问！'.format(self._url) + ' ' + res__.text[:100]}
                return {'code': 0, 'new_url': new_url,
                        'response': '域名{}经过跳转可以访问！新地址{}'.format(self._url, new_url) + ' ' + res__.text[:100]}
        else:
            return {'code': 0, 'response': '域名{}可以访问！'.format(self._url) + res.text[:100]}

    # 初始化实例属性
    def __init__(self):
        self._url = ''
        self._header = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)',
            'Cookie': '',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.goods_infos = []
        self.goods_list = []
        self.platformName = []

    # 设置域名
    def set_url(self, url):
        self._url = url

    # 注册
    def register(self, username='', password='', sex='', qqNumber='', pid=''):

        try:

            # 页面有一定概率访问超时，用while循环访问页面
            while True:
                try:
                    response = requests.get(url=self._url, headers=self._header)
                except BaseException as e:
                    print('- process - {} - 连接超时，10秒后重新连接...'.format(pid))
                    time.sleep(10)
                    continue
                if response.status_code not in [200, 201]:
                    print('- process - {} - 连接超时，10秒后重新连接...'.format(pid))
                    time.sleep(10)
                    continue
                else:
                    print('- process - {} - 连接成功...'.format(pid))
                    time.sleep(10)
                    break

            # 处理跳转
            # print(response.text.decode('utf-8'))
            if response.text == '页面跳转中~' or 'è¿å¥ä¸­' in response.text:
                result = re.findall(r"http:\/\/(.*)", self._url)
                self._header['Cookie'] = 'domain_jump={}; okdomain_jump={}'.format(result[0], result[0])
                self._header['Referer'] = self._url
                # 重定向访问
                response = requests.get(url=self._url + '?m=Home&c=DomainJump&a=index', headers=self._header,
                                        verify=False)
                # 保存cookies后再次访问
                for k, v in response.cookies.get_dict().items():
                    self._header['Cookie'] += '{}={}; '.format(k, v)
                response = requests.get(url=self._url + '/index.php', headers=self._header, verify=False)

            # 获取第一个商品的地址
            try:
                url = self._url + \
                      etree.HTML(response.text).xpath(r"//div[@class='div_url col-xs-6 col-sm-3 col-md-2']//a/@href")[0]
            # 动态加入数据会报错，此时直接从javascript标签用正则表达式获取数据
            except BaseException as e:
                # print('- process - {} - 域名{}注册失败,网站结构变化 {}'.format(pid, self._url, e))
                # return self._url
                pattern = re.compile(r".*goods_list\s=(.*?);")
                result = re.findall(pattern, response.text)[0][2:-1].split('},')
                for elem in result:
                    if elem[-1] != '}':
                        elem += '}'
                    elem = json.loads(elem.encode('utf-8'))
                    self.goods_list.append(elem)
                url = self._url + '/index.php?m=home&c=goods&a=detail&id={}&goods_type={}'.format(
                    self.goods_list[0]['id'],
                    self.goods_list[0][
                        'goods_type'])
            try:
                # 构造注册的post地址
                url_post = url.replace('home', 'Home').replace('goods', 'User').replace('detail', 'register').replace(
                    'User_type', 'goods_type')
                pattern = re.compile(self._url + r"/index\.php\?m=home&c=goods&a=detail&id=(\d+)&goods_type=(\d+)")
                id = pattern.match(url).group(1)
                goods_type = pattern.match(url).group(2)

                # 访问验证码图片地址，获取图片信息
                num = random.randint(0, 1548900677275)
                url_code = self._url + '/index.php?m=Home&c=User&a=verify_code&random=' + str(num)
                response = requests.get(url=url_code, headers=self._header)
                verify_text = ocr.discern(response.content)['result']

                # 访问图片后保存cookie
                cookies = response.cookies.get_dict()
                for key, value in cookies.items():
                    self._header['Cookie'] += '{}={}'.format(key, value)

                data_post = {
                    'username': '',
                    'username_password': '',
                    'sendpass_username': '',
                    'reg_username': username,
                    'reg_password': password,
                    'reg_sex': sex,
                    'reg_qq': qqNumber,
                    'code': verify_text,
                    'id': id,
                    'goods_type': goods_type,
                }

                # 注册
                time.sleep(1)
                res = requests.post(url=url_post, data=data_post, headers=self._header)
                res_ = json.loads(res.text.encode('utf-8'))
                if res_['status'] == 0:
                    print('- process - {} - 域名{}注册失败，失败原因:{}'.format(pid, self._url, res_['info']))
                    return self._url
                else:
                    print('- process - {} - 域名{}注册成功!'.format(pid, self._url))
            except BaseException as e:
                print('- process - {} - 域名{}注册失败,网站结构变化 {}'.format(pid, self._url, e))
                return self._url
        except BaseException as e:
            print('- process - {} - 域名{}注册失败,网站结构变化 {}'.format(pid, self._url, e))
            return self._url

    # 登录第一个商品页面，获取cookie
    def login(self, username='', password='', pid=''):

        # 页面有一定概率访问超时，用while循环访问页面
        while True:
            response = requests.get(url=self._url + '/index.php', headers=self._header)

            if response.status_code != 200:
                print('- process - {} - 连接超时，5秒后重新连接...'.format(pid))
                time.sleep(3)
                continue
            else:
                print('- process - {} - 连接成功...'.format(pid))
                s = requests.session()
                s.keep_alive = False
                time.sleep(1)
                break

        # 处理跳转
        # print(response.text.decode('utf-8'))
        if response.text == '页面跳转中~' or 'è¿å¥ä¸­' in response.text:
            result = re.findall(r"http:\/\/(.*)", self._url)
            self._header['Cookie'] = 'domain_jump={}; okdomain_jump={}'.format(result[0], result[0])
            self._header['Referer'] = self._url
            # 重定向访问
            response = requests.get(url=self._url + '?m=Home&c=DomainJump&a=index', headers=self._header, verify=False)
            # 保存cookies后再次访问
            for k, v in response.cookies.get_dict().items():
                self._header['Cookie'] += '{}={}; '.format(k, v)
            response = requests.get(url=self._url + '/index.php', headers=self._header, verify=False)

        # 获取第一个商品的地址,由于部分商城信息为javascript传入，所以做出if分支讨论
        try:
            # print(response.text)
            # print(etree.HTML(response.text).xpath(r"//div[@class='div_url col-xs-6 col-sm-3 col-md-2']//a/@href"))
            url = self._url + \
                  etree.HTML(response.text).xpath(r"//div[@class='div_url col-xs-6 col-sm-3 col-md-2']//a/@href")[0]

        # 动态加入数据会报错，此时直接从javascript标签用正则表达式获取数据
        except:
            pattern = re.compile(r".*goods_list\s=(.*?);")
            result = re.findall(pattern, response.text)[0][2:-1].split('},')
            for elem in result:
                if elem[-1] != '}':
                    elem += '}'
                elem = json.loads(elem.encode('utf-8'))
                self.goods_list.append(elem)
            url = self._url + '/index.php?m=home&c=goods&a=detail&id={}&goods_type={}'.format(self.goods_list[0]['id'],
                                                                                              self.goods_list[0][
                                                                                                  'goods_type'])

            # 构造post地址
        url_post = url.replace('home', 'Home').replace('goods', 'User').replace('detail', 'login').replace(
            'User_type',
            'goods_type')
        pattern = re.compile(self._url + r"/index\.php\?m=home&c=goods&a=detail&id=(\d+)&goods_type=(\d+)")
        id = pattern.match(url).group(1)
        goods_type = pattern.match(url).group(2)

        data_post = {
            'username': username,
            'username_password': password,
            'sendpass_username': '',
            'reg_username': '',
            'reg_password': '',
            'reg_sex': 0,
            'reg_qq': '',
            'code': '',
            'id': id,
            'goods_type': goods_type,
        }
        response = requests.post(url=url_post, data=data_post, headers=self._header)
        response_ = response.text
        response_dict = json.loads(response_)
        if response_dict['status'] == 1:
            print('- process - {} - 域名{}登录成功!'.format(pid, self._url))
            cookies = response.cookies.get_dict()
            # 保存cookie
            for key, value in cookies.items():
                self._header['Cookie'] += '{}={}'.format(key, value)
        else:
            print('- process - {} - 域名{}登录失败，失败原因：{}'.format(pid, self._url, response_dict['info']))

    # 获取商品详细信息
    def get_goods_detail(self, username='', password='', pid=''):

        # # 页面有一定概率访问超时，用while循环访问页面
        # while True:
        response = requests.get(url=self._url + '/index.php', headers=self._header)
        # # 关闭多余链接
        # s = requests.session()
        # s.keep_alive = False
        # if response.status_code != 200:
        #     print('连接超时，5秒后重新连接...')
        #     time.sleep(3)
        #     continue
        # else:
        #     print('连接成功...')
        #     s = requests.session()
        #     s.keep_alive = False
        #     time.sleep(1)
        #     break

        # 以商品内容为根节点，逐个访问
        try:
            platformName = etree.HTML(response.text).xpath(r"//div[@class='container-fluid menu']//strong/text()")[0]
        except:
            platformName = '无名'
        # 平台去除重复信息
        goodsinfos = etree.HTML(response.text).xpath(r"//div[@class='div_url col-xs-6 col-sm-3 col-md-2']")
        if goodsinfos:
            i = 0
            for goodsinfo in goodsinfos:
                i += 1
                goods = {}
                goods['No'] = i
                goods['platformName'] = platformName
                goods['goodsTitle'] = goodsinfo.xpath(r".//a/img/@title|.//a/div/h4/text()")[0]
                goods['href'] = self._url + goodsinfo.xpath(r".//a/@href")[0]
                # 去重复
                findresult = mongohelper.search('ninefivecommunity', 'href', goods['href'])
                if findresult:
                    print(' - process - {} - 当前商品信息已存在数据库表格中！ - {}'.format(pid, goods['href']))
                    continue
                # 针对每个商品的连接，继续访问，获取商品信息
                while True:
                    response = requests.get(url=goods['href'], headers=self._header)
                    # 关闭多余链接
                    s = requests.session()
                    s.keep_alive = False
                    if response.status_code != 200:
                        print('- process - {} - 连接超时，5秒后重新连接...'.format(pid))
                        time.sleep(3)
                        continue
                    else:
                        if "exit_login_a clipboard_btn" in response.text:
                            print('- process - {} - 连接成功，登录成功，正在获取第{}条数据...'.format(pid, goods['No']))

                            # 获取单价
                            try:
                                goods['goodsPrice'] = \
                                    etree.HTML(response.text).xpath(
                                        r"//ul[@class='card_info']//span[@class='user_unit_rmb']/text()")[0]
                            except Exception as e:
                                goods['goodsPrice'] = ''
                            # 获取商品id与goods_type
                            try:
                                pattern = re.compile(
                                    self._url + r"/index\.php\?m=home&c=goods&a=detail&id=(\d+)&goods_type=(\d+)")
                                goods['goods_id'] = pattern.match(goods['href']).group(1)
                                goods['goods_type'] = pattern.match(goods['href']).group(2)
                                # del goods['href']
                            except Exception as e:
                                goods['goods_id'] = ''
                                goods['goods_type'] = ''
                            # 获取最小与最大购买数
                            try:
                                count = etree.HTML(response.text).xpath(
                                    r"//form[@class='order_post_form']/ul[1]//input[@name='need_num_0']/@placeholder")[
                                    0]
                                pat = re.compile(r".*?(\d+)-(\d+).*")
                                goods['goods_min'] = pat.match(count).group(1)
                                goods['goods_max'] = pat.match(count).group(2)
                            except Exception as e:
                                goods['goods_min'] = ''
                                goods['goods_max'] = ''
                            print(goods)
                            # 进程互斥锁
                            mutex = Lock()
                            print(' - process - {} - 上锁！'.format(pid))
                            print(' - process - {} - 正在写入信息 '.format(pid), goods)
                            mutex.acquire()
                            mongohelper.add('ninefivecommunity', goods, pid)
                            mutex.release()
                            print(' - process - {} - 解锁！'.format(pid))
                            print(' - process - {} - 写入完成！ '.format(pid), goods)
                            break
                        elif '模型异常' in response.text:
                            break
                        else:
                            print('- process - {} - 连接成功，登录失败，重新登录...'.format(pid))
                            time.sleep(5)
                            self.login(username, password)
                            continue
            print('- process - {} - 域名为{}数据采集结束！'.format(pid, self._url))
        else:
            i = 0
            for goodsinfo in self.goods_list:
                i += 1
                goods = {}
                goods['No'] = i
                goods['platformName'] = platformName
                goods['goodsTitle'] = goodsinfo['title']
                goods['href'] = self._url + '/index.php?m=home&c=goods&a=detail&id={}&goods_type={}'.format(
                    goodsinfo['id'], goodsinfo['goods_type'])
                # 去重复
                findresult = mongohelper.search('ninefivecommunity', 'href', goods['href'])
                if findresult:
                    print(' - process - {} - 当前商品信息已存在数据库表格中！ - {}'.format(pid, goods['href']))
                    continue
                # 针对每个商品的连接，继续访问，获取商品信息
                while True:
                    response = requests.get(url=goods['href'], headers=self._header)
                    # 关闭多余链接
                    s = requests.session()
                    s.keep_alive = False
                    if response.status_code != 200:
                        print('- process - {} - 连接超时，5秒后重新连接...')
                        time.sleep(3)
                        continue
                    else:
                        if "exit_login_a clipboard_btn" in response.text:
                            print('- process - {} - 连接成功，登录成功，正在获取第{}条数据...'.format(pid, goods['No']))

                            # 获取单价
                            try:
                                goods['goodsPrice'] = \
                                    etree.HTML(response.text).xpath(
                                        r"//ul[@class='card_info']//span[@class='user_unit_rmb']/text()")[0]
                            except Exception as e:
                                goods['goodsPrice'] = ''
                            # 获取商品id与goods_type
                            try:
                                pattern = re.compile(
                                    self._url + r"/index\.php\?m=home&c=goods&a=detail&id=(\d+)&goods_type=(\d+)")
                                goods['goods_id'] = pattern.match(goods['href']).group(1)
                                goods['goods_type'] = pattern.match(goods['href']).group(2)
                                # del goods['href']
                            except Exception as e:
                                goods['goods_id'] = ''
                                goods['goods_type'] = ''
                            # 获取最小与最大购买数
                            try:
                                count = etree.HTML(response.text).xpath(
                                    r"//form[@class='order_post_form']/ul[1]//input[@name='need_num_0']/@placeholder")[
                                    0]
                                pat = re.compile(r".*?(\d+)-(\d+).*")
                                goods['goods_min'] = pat.match(count).group(1)
                                goods['goods_max'] = pat.match(count).group(2)
                            except Exception as e:
                                goods['goods_min'] = ''
                                goods['goods_max'] = ''
                            # 进程互斥锁
                            mutex = Lock()
                            print(' - process - {} - 上锁！'.format(pid))
                            print(' - process - {} - 正在写入信息 '.format(pid), goods)
                            mutex.acquire()
                            mongohelper.add('ninefivecommunity', goods, pid)
                            mutex.release()
                            print(' - process - {} - 解锁！'.format(pid))
                            print(' - process - {} - 写入完成！ '.format(pid), goods)
                            break
                        elif '模型异常' in response.text:
                            break
                        else:
                            print('- process - {} - 连接成功，登录失败，重新登录...')
                            time.sleep(3)
                            # self.login(username, password)
                            continue
            print('- process - {} - 域名为{}数据采集结束！'.format(pid, self._url))

    def test(self, url):
        res = requests.get(url=url, headers=self._header)
        # print(res.text)
        if 'è¿å¥ä¸­~' in res.text or '页面跳转中' in res.text:
            print('获取重定向cookie后继续采集...')

            a = res.cookies.get_dict().items()
            for k, v in a:
                self._header['Cookie'] += '{}={}; '.format(k, v)

            res = requests.get(url=url + '/index.php?m=Home&c=DomainJump&a=index', headers=self._header)
            # print(res.text)
            b = res.cookies.get_dict().items()
            for k, v in b:
                self._header['Cookie'] += '{}={}; '.format(k, v)

            print(self._header['Cookie'])
            return True
        else:
            return False

    def set_cookie(self, cookie):
        self._header['Cookie'] = cookie


class Handle_NineFive():
    # 过滤所有url，将可以访问的存入新的列表中
    @classmethod
    def filter(cls, index, last, l, pid, length, urls):
        print('process - {} - start'.format(pid))
        for url in urls[index:last]:
            p = Platforminfo_NineFive()
            p.set_url(url)
            result = p.filter()
            print('process - {} - '.format(pid), result)
            # 判断信息，是否可以访问，可以访问就存入新的列表中
            if result['code'] == 0:
                if result.get('new_url', ''):
                    l.append(result['new_url'])
                    continue
                l.append(url)
            print(' - process - {} - 当前已过滤的网站:'.format(pid), l)
        print(' - process - {} - 可以访问的网站:'.format(pid), l)
        print(' - process - {} - over'.format(pid))

    # 获取所有可访问的url的商品信息
    @classmethod
    def collection(cls, index, last, l, pid, length, urls):
        print('process - {} - start'.format(pid))
        i = 0
        for url in urls[index:last]:
            while True:
                try:
                    time.sleep(3)
                    i += 1
                    # 先测试这个链接是否有更换域名
                    print('- process - {} - 开始采集第{}条url...'.format(pid, i))
                    p = Platforminfo_NineFive()
                    p.set_cookie('')
                    p.set_url(url)
                    result = p.test(url)
                    if result:
                        p.set_url(url)
                    else:
                        pass
                    p.login('linx10001', '987654322', pid)
                    p.get_goods_detail('linx10001', '987654322', pid)
                    l.append(url)
                    print('- process - {} - 当前已采集的网站:'.format(pid), l)
                    break
                except BaseException as e:
                    print('- process - {} - 域名：{}采集异常! 过10秒钟后继续尝试！{}'.format(pid, url, e))
                    print('- process - {} - 当前已采集的网站:'.format(pid), l)
                    time.sleep(10)
                    continue
        print('- process - {} - 已采集的网站:'.format(pid), l)
        print('process - {} - over'.format(pid))

    # 批量注册
    @classmethod
    def register(cls, index, last, l, pid, length, urls):
        print('process - {} - start'.format(pid))
        for url in urls[index:last]:
            p = Platforminfo_NineFive()
            p.set_url(url)
            res = p.register('linx10001', '987654322', '0', '524802906', pid)
            # 无返回值说明注册成功
            if not res:
                l.append(url)
            print(' - process - {} - 当前已注册的网站:'.format(pid), l)
        print(' - process - {} - 已注册网站：'.format(pid), l)
        print(' - process - {} - over'.format(pid))


if __name__ == '__main__':
    pass
    # 设置域名

    # platform.set_url('http://www.fyxbd.com') #蚂蚁社区 已注册
    # platform.set_url('http://liebao.95jw.cn') #猎豹社区 已注册
    # platform.set_url('http://qqkami.95jw.cn') #熊猫社区 已注册
    # platform.set_url('http://mohan.ssgnb.95jw.cn')  # javascript动态传递数据
    # platform.set_url('http://jiuban.95jw.cn') #久伴社区 已注册
    # platform.set_url('http://v8.95jw.cn') #v8社区 已注册 已测试
    # platform.set_url('http://xiaochao.95jw.cn')#已注册 ce
    # platform.set_url('http://kuaishua.95jw.cn') #Domain Error!pt-v3!kuaishua.95jw.cn 域错误
    # platform.set_url('http://chaosu.95jw.cn')#已注册 ce
    # platform.set_url('http://sz666.95jw.cn')#已注册 已测试
    # platform.set_url('http://guaqq.95jw.cn') #Domain Error!pt-v3!guaqq.95jw.cn 域错误
    # platform.set_url('http://tianyuwl.95jw.cn') #已注册 以测试
    # platform.set_url('http://38mao.95jw.cn') #猫猫卡密 已测试
    # platform.set_url('http://yanxi.95jw.cn') #已注册 已测试
    # platform.set_url('http://wga.95jw.cn') #微光社区 已注册 已测试
    # platform.set_url('http://ab.95jw.cn')#阿彪社区 已注册 已测试

    # 注册
    # platform.register('linx01','987654322', '0', '410559855' )

    # 登录
    # platform.login('linx01', '987654322')
    #
    # # 获取商品详细信息
    # platform.get_goods_detail()

    # 将商品信息写入excel表格
    # generate_excel(platform.goods_infos)
