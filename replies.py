import requests
import re
import json
import time
from time import sleep
import random

def bv2av(BV:str):
    '''
    字典法，BV号转化为av号
    '''
    dic={'1':13,'2':12,'3':46,'4':31,'5':43,'6':18,'7':40,'8':28,'9':5,
        'A':54,'B':20,'C':15,'D':8,'E':39,'F':57,'G':45,'H':36,'J':38,'K':51,
        'L':42,'M':49,'N':52,'P':53,'Q':7,'R':4,'S':9,'T':50,'U':10,'V':44,'W':34,
        'X':6,'Y':25,'Z':1,'a':26,'b':29,'c':56,'d':3,'e':24,'f':0,'g':47,'h':27,
        'i':22,'j':41,'k':16,'m':11,'n':37,'o':2,'p':35,'q':21,'r':17,'s':33,
        't':30,'u':48,'v':23,'w':55,'x':32,'y':14,'z':19}
    lst1=[dic[i]for i in BV]
    l=len(lst1)
    lst2=[6,2,4,8,5,9,3,7,1,0]
    lst3=[lst1[i]*(58**lst2[i]) for i in range(l)]
    s=sum(lst3)
    t=s-100618342136696320
    bint=bin(t)
    t0=177451812
    bint0=bin(t0)
    av=int(bint,2)^int(bint0,2)
    return str(av)

def trans_date(v_timestamp):
    '''
    10位时间戳转换为时间字符串
    '''
    timeArray = time.localtime(v_timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime

def header(*param):
    '''
    返回请求头
    '''
    headers = {
        'authority': 'api.bilibili.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'origin': 'https://www.bilibili.com',
        'referer': param[0],
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'
    }
    # 可以加cookie，不加也行
    if len(param) == 2:
        headers['cookie'] = param[1]
    
    return headers

def delay_request():
    '''
    延时等待函数，防止反爬取
    '''
    delay_seconds = random.uniform(3, 10)
    sleep(delay_seconds)

def abv_get(url:str):
    '''
    从url中获取av号
    '''
    if url.startswith('https://www.bilibili.com/video/'):
        strs = url.split('https://www.bilibili.com/video/')[1].split('/')[0]
        if strs.startswith('av'):
            av = strs.split('av')[1]
        elif strs.startswith('BV'):
            BV = strs.split('BV')[1]
            av = bv2av(BV)
        else: 
            print("can't find av or bv, error type of url.")
        return av
    else:
        print("error type of url.")
    
def root_api_make(url, next_num, type, mode, plat):
    '''
    构造评论api，next_num为页数
    '''
    av = abv_get(url)
    # 模板：https://api.bilibili.com/x/v2/reply/main?&jsonp=jsonp&next=<1>&type=<1>&oid=<aid>&mode=<3>&plat=<1>&_=<not important>
    api_url = f'https://api.bilibili.com/x/v2/reply/main?\
jsonp=jsonp&\
next={next_num}&\
type={type}&\
oid={av}&\
mode={mode}&\
plat={plat}'
    return api_url

def root_comment_get(url, next_num):
    '''
    获取根评论数据
    '''
    type = 1
    mode = 3
    plat = 1
    root_api_url = root_api_make(url, next_num, type, mode, plat)
    headers = header(url)
    response = requests.get(root_api_url,headers = headers)
    jsr = response.json()
    with open ('root_comment.json', mode='a', encoding='utf-8') as r:
        json.dump(jsr, r)
    data = jsr['data']
    return data

def secondary_comments_get(url, pn, root):
    '''
    获取次级评论数据
    '''
    av = abv_get(url)
    secn_url = f'https://api.bilibili.com/x/v2/reply/reply?\
jsonp=jsonp&\
pn={pn}&\
type=1&\
oid={av}&\
ps=10&\
root={root}'
    headers = header(url)
    response = requests.get(secn_url,headers = headers)
    jss = response.json()
    with open ('secondary_comment.json', mode='a', encoding='utf-8') as r:
        json.dump(jss, r)
    datas = jss['data']
    return datas
    
def get_replies(url, data):
    '''
    获取replies部分内容
    '''
    replies_root = data['replies']
    comment_list = []
    for reply in replies_root:
        comment_root = reply['content']['message']
        root = reply['rpid']
        pn = 1
        datas = secondary_comments_get(url, pn, root)
        comment_secn_all = ''
        while(datas['replies'] != [] and type(datas['replies'])==list):
            replies_secn = datas['replies']
            for replys in replies_secn:
                comment_secn = replys['content']['message']
                comment_secn_all = comment_secn_all+'+++'+comment_secn+'\n'
            pn += 1
            datas = secondary_comments_get(url, pn, root)
        comment = f'root:{root}\n'+comment_root+'\n'+'secondary:'+'\n'+ comment_secn_all
        comment_list.append(comment)
    with open ('comment.csv', mode='a', encoding='utf-8') as r:
        for comment in comment_list:
            r.write(comment+'\n'+'**********************************'+'\n')

def get_cid(url:str):
    '''
    通过视频链接获取视频cid
    '''
    aid = abv_get(url)
    # pagelist中可使用aid（即av号）获取cid：https://api.bilibili.com/x/player/pagelist?aid=<aid>
    url_cid = f'https://api.bilibili.com/x/player/pagelist?aid={aid}'
    headers = header(url)
    res = requests.get(url_cid, headers=headers)
    data = res.json()['data']
    cid = data[0]['cid']
    part = data[0]['part']
    return cid, part

def get_danmuku(url:str):
    '''
    获取视频弹幕并保存至xml文件
    '''
    cid, part = get_cid(url)
    #B站弹幕api接口：https://comment.bilibili.com/<cid>.xml
    url_xml = f'https://comment.bilibili.com/{cid}.xml'  
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0;Win64;x64) AppleWebKit/537.36(KHTML, likeGecko) Chrome/80.0.3987.163Safari/537.36"
    }
    res = requests.get(url_xml,headers = headers).content.decode('utf-8') 
    with open(f'./{part}.xml', mode='w', encoding='utf-8') as w:
        w.write(res)
    # 返回xml格式数据
    return res

def xml_to_text(xml_data):
    '''
    将xml中的弹幕文本保存至txt文件中（可选）
    '''
    pattern = re.compile(r'<d p=".*?">(.*?)</d>')
    txt_data_list = re.findall(pattern, xml_data)
    with open ('danmuku.txt', mode='w', encoding='utf-8') as danmu:
        for txt_data in txt_data_list:
            danmu.write(txt_data+'\n')

def get_all():
    url = input("please input the video's url: ")
    _ = get_danmuku(url)
    print('danmu has been gotten.')
    next_num = 1
    data = root_comment_get(url, next_num)
    while (data['replies'] != [] and type(data['replies'])==list):
        get_replies(url, data)
        print(f'page num: {next_num}' )
        next_num += 1
        delay_request()
        data = root_comment_get(url, next_num)
    print('comments have benn gotten.')
    print('all down.')

if __name__ == '__main__':
    get_all()