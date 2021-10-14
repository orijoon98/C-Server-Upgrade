import sys
sys.path.append("/home/pi/C-Server/env/lib/python3.9/site-packages")

from pymongo import MongoClient
import urllib.request
from urllib.request import urlopen
from bs4 import BeautifulSoup
import schedule
import time
import json
import ssl
import json
from collections import OrderedDict

def setNew(): # 가장 최근 회차 번호 업데이트
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    url = 'https://dhlottery.co.kr/gameResult.do?method=byWin&wiselog=H_C_1_1'
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    text = ""

    for meta in soup.head.find_all('meta'):
        text += str(meta.get('content'))
        text += '\n'

    index = 0
    numbers = []
    flag = False

    for x in text:
        if x >= '0'and x <= '9':
            if flag == False:
                numbers.append("")
            numbers[index] += str(x)
            flag = True
        else:
            if flag == True: 
                index += 1
                flag = False

    return int(numbers[0]) # 가장 최근 회차 번호
    # numbers index 별 정보
    # 0 : 회차
    # 1 ~ 6 : 당첨 번호
    # 7 : 보너스 번호
    # 9 : 1등 당첨 인원 수
    # 11 ~ end : 1등 1인당 당첨 금액

def setData(): # 토요일 오후 10시마다 호출
    global LottoList
    LottoList = OrderedDict()
    
    LottoList["datas"] = []

    new = setNew() + 1 # 가장 최근 회차 + 1, 다음에 받아올 회차
    old = new - 53  # 가장 최근 회차 - 52

    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    for i in range(old, new): # 최근 1년치 정보
        url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=" + str(i)
        result = urlopen(url).read()
        lotto = json.loads(result)

        drwNoDate = lotto["drwNoDate"]
        drwNo = lotto["drwNo"]
        drwtNo1 = lotto["drwtNo1"]
        drwtNo2 = lotto["drwtNo2"]
        drwtNo3 = lotto["drwtNo3"]
        drwtNo4 = lotto["drwtNo4"]
        drwtNo5 = lotto["drwtNo5"]
        drwtNo6 = lotto["drwtNo6"]
        bnusNo = lotto["bnusNo"]
        firstWinamnt = lotto["firstWinamnt"]
        firstAccumamnt = lotto["firstAccumamnt"]
        firstPrzwnerCo = lotto["firstPrzwnerCo"]
        totSellamnt = lotto["totSellamnt"]

        LottoList["datas"].append({
            "drwNoDate":drwNoDate,
            "drwNo":drwNo,
            "drwtNo1":drwtNo1,
            "drwtNo2":drwtNo2,
            "drwtNo3":drwtNo3,
            "drwtNo4":drwtNo4,
            "drwtNo5":drwtNo5,
            "drwtNo6":drwtNo6,
            "bnusNo":bnusNo,
            "firstWinamnt":firstWinamnt,
            "firstAccumamnt":firstAccumamnt,
            "firstPrzwnerCo":firstPrzwnerCo,
            "totSellamnt":totSellamnt
        })

    print(json.dumps(LottoList, indent="\t"))

    client = MongoClient("localhost", 27017)
    db = client["lotto"]
    collection = db["lotto"]
    collection.delete_many({})
    collection.insert_one(LottoList)

    for col in collection.find():
        print(col)

#setData()

schedule.every().saturday.at("22:00").do(setData)

while True:
    schedule.run_pending()
    time.sleep(1)




