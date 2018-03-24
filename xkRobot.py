# -*- coding: utf-8 -*-
# @Time  : 2018/03/22
# @Author   : ZhaoEndong

import requests
import os
import PIL.Image as Image
from os import listdir
import math
import configparser
import threading
import time
import itchat
from pandas import DataFrame
from itchat.content import *
from pyecharts import Pie,Geo
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# http://itchat.readthedocs.io/zh/latest/ 微信插件官网
# https://segmentfault.com/a/1190000009420701 API说明

KEY = 'e1749901d86c49bbb8d00afb058547bd'
HELP = '''自定义功能可回复以下内容:
你是谁\t回复:1\n公众号\t回复:2\n头像拼图\t回复:3\n性别比例\t回复:4\n地理位置\t回复:5\n统计图表\t回复:6
其他内容将由机器人自动回复...'''

###########全局变量###########
global G_UserNameValue
global threads
global splitstr
global parameter
global picDir
global outputfile
global strtm
#主线程 实例
global mainInstance
#global value
# 步骤的提示语
global  dict_stepinfo
# 启动脚本前的提示语
global helpinfo
# 客户列表
global list_customer
# 用户数量id
global cnt
# 客户线程
global client_list

mutex = threading.Lock()
picDir = 'qr_test.png'
G_UserNameValue =None
mainInstance = itchat.new_instance()
threads = []
splitstr='_'
parameter='[parameter]'
helpinfo=''
dict_stepinfo = {}
list_customer = []
cnt = 0
client_list = []
strtm = time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time()))
outputfile = open("log/log_%s.txt"%strtm, "a+")

# 机器人的自动回复
def get_response(msg):
    # 构造了要发送给服务器的数据
    apiUrl = 'http://www.tuling123.com/openapi/api'
    data = {
        'key': KEY, # 如果这个Tuling Key不能用，那就换一个
        'info': msg, # 这是我们发出去的消息
        'userid' : 'wechat-robot', # 这里你想改什么都可以
    }
    try:
        r = requests.post(apiUrl, data=data).json()
        return r.get('text')
    except:
        # 返回一个None
        return


#客户线程类
class itchat_client (threading.Thread):
    #初始化函数
    def __init__(self, threadID, name,UserNameValue,msgstr,friendsnum=100):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.UserNameValue = UserNameValue
        self.friendsnum = friendsnum
        self.msgstr = msgstr

        self.picDir = 'qr/%s.png'%(UserNameValue.replace('@','qr')[0:7])
        self.step = 0 #0-初始化   1-完成 向客户发送二维码  
        self.newInstance = itchat.new_instance()

    #qrCallBack 函数
    def qrsendtouser(self,uuid, status, qrcode):
        global mainInstance
        strtm = time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time()))
        print('qrsendtouser')
        with open(self.picDir, 'wb') as f:
            f.write(qrcode)
        print('write success')
        if self.step < 1:
            if mutex.acquire():
                print('c send QR G_UserNameValue=',self.UserNameValue)
                mainInstance.send('@img@%s' %(self.picDir),self.UserNameValue)
                mainInstance.send('记得是一个手机扫另一个手机才有效哦~',self.UserNameValue)
                print('c send QR end')
                self.step = 1
                mutex.release()
            else:
                print('mutex error')
            print('send success')

    #run 函数
    def run(self):
        global mainInstance
        print('Welcome using [ xkRobot ] version: beta1')
        # ###################################开始程序###########################################
        try:
            self.newInstance.auto_login(picDir=self.picDir,qrCallback=self.qrsendtouser)
            list_dict_friends = self.newInstance.get_friends()
            friendsnum = len(list_dict_friends)
            funstr = self.msgstr


            # 生成地理坐标图
            def get_geo():
                geo = Geo("朋友所在地分布", "data from 微信", title_color="#fff",title_pos="center", width=1000, height=800, background_color='#404a59')
                attrs, value = geo.cast(data['City'])
                geo.add("", attrs, value, visual_range=[0, 200], visual_text_color="#fff",  symbol_size=15, is_visualmap=True)
                geolfile = self.UserNameValue+'-geo.html'
                geo.render(geolfile)
                mainInstance.send('@fil@%s'% geolfile,self.UserNameValue)

            # 生成Excel文件
            def get_excel():
                frame = DataFrame(data)
                excellfile = self.UserNameValue+'.csv'
                frame.to_csv(excellfile, index=True,encoding="utf8")
                mainInstance.send('@fil@%s' % excellfile,self.UserNameValue)

            # 生成性别比例图
            def get_sexrate():
                male=female=other=0
                for i in list_dict_friends[1:]:
                    sex = i["Sex"]
                    if sex==1:
                        male+=1
                    elif sex ==2:
                        female+=1
                    else :
                        other +=1
                total = len(list_dict_friends[1:])
                friendsInfo = '好友总数:{0}\n男性好友:{1}\n女性好友:{2}\n其他好友:{3}\n'.format(total,int(male),int(female),int(other))
                mainInstance.send_msg(friendsInfo,self.UserNameValue)

                attr=["男性好友","女性好友","其他好友"]
                pie=Pie("性别比例")
                sexs = [int(male),int(female),int(other)]
                pie.add("",attr,sexs,is_lable_show=True)
                hfile = self.UserNameValue+'-sex.html'
                pie.render(hfile)
                # 读取网页下载图片
                def webscreen():
                    url = hfile
                    driver = webdriver.Chrome(r'D:\Program Files\chromedriver.exe')
                    driver.get(url)
                    element = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'[data-zr-dom-id=zr_0]')))
                    actions = ActionChains(driver)
                    actions.move_to_element_with_offset(element, 775, 175)
                    actions.click()
                    # C:\Users\Administrator\Downloads 下载路径
                    actions.perform()
                    driver.close()
                webscreen()
                # 发给用户
                sfile = r'C:\Users\Administrator\Downloads\性别比例.png'
                mainInstance.send('@fil@%s' % sfile,self.UserNameValue)

            # 生成用户好友拼图
            def get_headimgs():
                user = list_dict_friends[0]["UserName"]
                print('登录名称：',user)
                os.mkdir(user)
                num = 0
                for i in list_dict_friends:
                    img = self.newInstance.get_head_img(userName=i["UserName"])
                    fileImage = open(user + "/" + str(num) + ".jpg",'wb')
                    fileImage.write(img)
                    fileImage.close()
                    num += 1
                pics = listdir(user)
                numPic = len(pics)
                print('好友总数：',numPic-1)
                eachsize = int(math.sqrt(float(640 * 640) / numPic))
                print('头像大小：',eachsize,'px')
                numline = int(640 / eachsize)
                toImage = Image.new('RGB', (640, 640))
                print(numline)
                x = 0
                y = 0
                for i in pics:
                    try:
                        #打开图片
                        img = Image.open(user + "/" + i)
                    except IOError:
                        print("Error: 没有找到文件或读取文件失败")
                    else:
                        #缩小图片
                        img = img.resize((eachsize, eachsize), Image.ANTIALIAS)
                        #拼接图片
                        toImage.paste(img, (x * eachsize, y * eachsize))
                        x += 1
                        if x == numline:
                            x = 0
                            y += 1
                toImage.save(user + ".jpg")
                mainInstance.send_image(user + ".jpg", self.UserNameValue)

            #定义一个函数，用来爬取各个变量
            def get_var(var):
                variable = []
                for i in list_dict_friends:
                    value = i[var]
                    variable.append(value)
                return variable
            NickName = get_var("NickName")
            Sex = get_var('Sex')
            Province = get_var('Province')
            City = get_var('City')
            Signature = get_var('Signature')
            data = {'NickName': NickName, 'Sex': Sex, 'Province': Province,'City': City, 'Signature': Signature}
            if u'头像拼图' == funstr:
                get_headimgs()
            elif u'性别比例' == funstr:
                get_sexrate()
            elif u'地理位置' == funstr:
                get_geo()
            elif u'统计图表' == funstr:
                get_excel()
            else:
                # 原始的检测好友数量的代码
                i=0
                for x in range(0,friendsnum):
                    NickName = list_dict_friends[x]['NickName']
                    UserNameValue = list_dict_friends[x]['UserName']
                    self.newInstance.send('@img@qr/turing.png',UserNameValue)
                    time.sleep(0.2)
                    print(x,'OK')
                    i=i+1
                if mutex.acquire():
                    print('c thread end G_UserNameValue=',self.UserNameValue)
                    mainInstance.send('完成!共检测【%d】个好友'%i,self.UserNameValue)
                    print('c thread end ')
                    self.step = 1
                    mutex.release()
                else:
                    print('thread end mutex error')

        except Exception as e:
            myException("STEP OF startdelete mainprocess","startdelete",e)
        else:
            pass
        print('thread end')

# 没有下单的客户信息 Customer类
class Customer(object):
    def __init__(self,nickname,namevalue,friendsnum,step):
        global cnt
        self.id = cnt
        self.nickname = nickname
        self.namevalue = namevalue
        self.friendsnum = friendsnum
        self.step = step
        self.shouldpay = 1.0
        cnt += 1

#############公共函数#############
#异常处理
def myException(whichStep,log,e):
    global outputfile
    strtm = time.strftime('%Y_%m_%d__%H_%M_%S',time.localtime(time.time()))
    str = "###%s[Exception]:%s [Log]:%s [e]:%s \n"%(strtm,whichStep,log,e)
    print(str)
    try:
        outputfile.write(str)
    except Exception as e:
        print(e)

# 获得对应的回复信息
def getreply(msgstr,who):
    global list_customer,splitstr, parameter,client_list,mainInstance,G_UserNameValue
    thiscustomer=''
    #获得这个类
    try:
        tembool=0 #此用户 没有记录过
        for x in range(0,len(list_customer)):
            if list_customer[x].namevalue == who :
                thiscustomer = list_customer[x]
                tembool = 1 #被记录过
                break
        if tembool == 0:
            #新增用户
            thiscustomer = Customer('null',who,friendsnum=100,step=0)
            list_customer.append(thiscustomer)
    except Exception as e:
        #新增用户
        thiscustomer = Customer('null',who,friendsnum=100,step=0)
        list_customer.append(thiscustomer)
    else:
        pass
    # 0 0= 在的亲 [呲牙] 
    print('#',thiscustomer.step)
    if thiscustomer.step == 0:
        thiscustomer.step = 1
        return dict_stepinfo[0]
    # 1=请问您的好友数量多少呢？ [呲牙]
    elif thiscustomer.step == 1:
        thiscustomer.step = 2
        return dict_stepinfo[1]
    # 2=您需要测试的好友数为[parameter],向我转账[parameter]元立刻开始测试[爱心]
    elif thiscustomer.step == 2:
        print(msgstr)
        try:
            num = int(msgstr)
            if num >0 and num < 9999 :
                money = num/200
                if money == 0:
                    money = 1
                elif money > 2:
                    money = money + 2
                returnvalue = dict_stepinfo[2].replace(parameter,msgstr,1).replace(parameter,str(money))
                thiscustomer.friendsnum = num
                thiscustomer.shouldpay = float(money)
                thiscustomer.step = 3
                return returnvalue
            else:
                return '发给我 你的好友数量哦~'
        except Exception as e:
            myException("STEP OF get num of friends","getreply msgstr=%s"%msgstr,e)
            return '发给我 你的好友数量哦~'
    # 3=等待付款中哦[呲牙] 转账后立即开始(第三部测试的时候注释了测试完成需要放开)
    # elif thiscustomer.step == 3 :
    #     return dict_stepinfo[3]
    #测试中，请稍等[呲牙]
    # elif thiscustomer.step == 3 :
    #     return dict_stepinfo[4]
    elif thiscustomer.step == 3 :
        try:
            if int(msgstr) == 1:
                G_UserNameValue = thiscustomer.namevalue

                newthread = itchat_client(1,'client_thread',thiscustomer.namevalue,msgstr,thiscustomer.friendsnum)
                newthread.start()
                client_list.append(newthread)
                thiscustomer.step=0
                return '生成二维码中，请稍等...'
        except Exception as e:
            myException("STEP OF confirm  start thread","last step == 2017  msgstr =%s"%msgstr,e)
            return '等待您回复【1】哦~'
        return '等待您回复【1】哦~'

# 初始化
def init():
    global helpinfo,dict_stepinfo
    cp = configparser.SafeConfigParser()
    cp.read('config.conf')
    helpinfo = cp.get('helpinfo','main')
    dict_stepinfo[0] = cp.get('step','0')
    dict_stepinfo[1] = cp.get('step','1')
    dict_stepinfo[2] = cp.get('step','2')
    dict_stepinfo[3] = cp.get('step','3')   
    dict_stepinfo[4] = cp.get('step','4')

##################主线程代码##################
try:
    #初始化
    init()
    #启动登陆程序
    mainInstance.auto_login(hotReload=True)

    # 监听转账信息 NOTE
    @mainInstance.msg_register([NOTE])
    def text_reply(msg):
        global list_customer,splitstr, parameter,helpinfo,mainInstance
        print('msg_register(NOTE) ',msg['Text'])
        mainInstance.send('%s: %s' % (msg['Type'], msg['Text']), msg['FromUserName'])
        if  msg['Text'].find('转账') > 0:
            try:
                #匹配用户
                thiscustomer=''
                who = msg['FromUserName']
                money = float(msg['Text'].split("转账")[-1].split('元')[0])
                print(money)
                #获得这个类
                tembool=0 #此用户 没有记录过
                for x in range(0,len(list_customer)):
                    if list_customer[x].namevalue == who and list_customer[x].shouldpay <= money:
                        thiscustomer = list_customer[x]
                        tembool = 1 #被记录过
                        break
                if tembool == 1:
                    thiscustomer.step = 2017
                    mainInstance.send('%s' % (helpinfo), msg['FromUserName'])
                else:
                    #此用户没有记录过
                    mainInstance.send('%s: %s' % ('多谢您的捐赠！',msg['Text']), msg['FromUserName'])

            except Exception as e:
                myException("STEP OF NOTE","get a note msg msgtext=%s"%msg['Text'],e)
                mainInstance.send('%s: %s' % ('操作异常，请联系管理员！',msg['Text']), msg['FromUserName'])
            else:
                pass

    # 回复文字信息 指导用户下单关注公众号与机器人聊天
    @mainInstance.msg_register([TEXT])
    def text_reply(msg):
        global mainInstance
        print('msg_register(TEXT) ',msg['Text'])
        if u'你是谁' in msg['Text']:
            mainInstance.send(u'我是稀客宝宝的小秘书\n请回复:机器人(空格)你想说的话,与机器人聊天\n比如:机器人 郑州天气',msg['FromUserName'])
        elif u'公众号' in msg['Text']:
            mainInstance.send('@img@qrcode.jpg',msg['FromUserName'])
            print('回复:\n 公众号二维码已发送，扫码关注\n')
            mainInstance.send(u'扫码关注:古乐坊')
        elif u'机器人' in msg['Text']:
            words = msg['Text'][4:]
            res = get_response(words)
            mainInstance.send(res,msg['FromUserName'])
        else:
            replystr = getreply(msg['Text'],msg['FromUserName'])
            mainInstance.send(replystr,msg['FromUserName'])

    # 收到好友邀请自动添加好友
    @mainInstance.msg_register([FRIENDS])
    def add_friend(msg):
        global list_customer,mainInstance
        print('msg_register(FRIENDS)')
        mainInstance.add_friend(**msg['Text']) # 该操作会自动将新好友的消息录入，不需要重载通讯录
        mainInstance.send_msg(u'您好，我是小客机器人', msg['RecommendInfo']['UserName'])
        #新建一个账户信息
        newcustomer = Customer('null',msg['FromUserName'],friendsnum=100,step=0)
        list_customer.append(newcustomer)

    # 以后需要扩展的功能
    @itchat.msg_register(['Picture', 'Recording', 'Attachment', 'Video'])
    def atta_reply(msg):
        msg.download(msg.fileName)
        # 下载的文件发送给发送者
        itchat.send_msg(u'文件已接收',msg.fromUserName)
        itchat.send('@%s@%s'%('img' if msg['Type']=='Picture' else 'fil',msg.fileName),msg.fromUserName)

    mainInstance.run()
except Exception as e:
    myException("STEP OF mainprocess","main",e)
    outputfile.close()
print('THE END')
