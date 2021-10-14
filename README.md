# C 서버 업그레이드

## 기존 서버

[C언어 HTTP 서버](https://www.notion.so/C-HTTP-426fa63fd6dc43f9b4866d1491d4dc59)

## 업그레이드 목록

- 데이터를 파일로 관리하지 않고 MongoDB로 관리
- data.html 을 파일 입출력이나 bash의 IORedirection 으로 작성하지 않고 서버에서 바디부분 작성
- 기존에는 서버를 따로 실행시키고 크롤링을 담당하는 파이썬 프로그램을 따로 실행 시켰었는데 서버만 실행해도 크롤링이 가능하도록 변경

## 순서

1. 파이썬으로 크롤링한 데이터 MongoDB에 저장하기
2. 서버에서 MongoDB에 저장된 데이터 받아오기
3. 서버에서 파이썬 프로그램 실행시키기

## 데이터 MongoDB에 저장

```python
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
```

기존에 사용했던 로또 데이터를 크롤링 하는 파이썬 코드를 조금 수정했다.

원래는 크롤링한 데이터를 lotto.json 이라는 파일에 저장했는데 파일 대신에 DB에 데이터를 저장해주기 위해 코드를 수정해줬다.

로컬로 MongoDB를 사용했고 추가된 코드는 다음과 같다.

```python
client = MongoClient("localhost", 27017)
db = client["lotto"]
collection = db["lotto"]
collection.delete_many({})
collection.insert_one(LottoList)
```

pymongo 라이브러리를 사용해서 간편하게 MongoDB에 접근할 수 있고 로컬 주소를 사용하고 포트는 기본 포트인 27017을 사용했다.

delete_many({}) 는 저장된 데이터를 모두 지우는 코드이다.

데이터가 업데이트 될 때마다 기존에 있던 데이터를 지우고 새롭게 업데이트된 데이터만 저장하게 구현했다.

## 서버에서 데이터 받아오기

```c
//server.h
int bind_lsock(int lsock, int port);
void fill_header(char *header, int status, long len, char *type);
void find_mime(char *ct_type, char *uri);
void handle_404(int asock);
void handle_500(int asock);
void http_handler(int asock);
void run_server();
```

```c
//server.c
void http_handler(int asock) {
    char header[BUF_SIZE];
    char buf[BUF_SIZE] = {};

    mongoc_client_t *client;
    mongoc_collection_t *collection;
    mongoc_cursor_t *cursor;
    const bson_t *doc;
    bson_t *query;

    mongoc_init ();

    client = mongoc_client_new ("mongodb://localhost:27017");
    collection = mongoc_client_get_collection (client, "lotto", "lotto");
    query = bson_new ();
    cursor = mongoc_collection_find_with_opts (collection, query, NULL, NULL);

    if (read(asock, buf, BUF_SIZE) < 0) {
        perror("[ERR] Failed to read request.\n");
        handle_500(asock);
        return;
    }

    char *method = strtok(buf, " ");
    char *uri = strtok(NULL, " ");
    if (method == NULL || uri == NULL) {
        perror("[ERR] Failed to identify method, URI.\n");
        handle_500(asock);
        return;
    }

    printf("[INFO] Handling Request: method=%s, URI=%s\n", method, uri);

    char safe_uri[BUF_SIZE];
    char *local_uri;
    struct stat st;

    strcpy(safe_uri, uri);
    if (!strcmp(safe_uri, "/"))
        strcpy(safe_uri, "/index.html");

    if (!strcmp(safe_uri, "/getdata"))
        strcpy(safe_uri, "/data.html");

    local_uri = safe_uri + 1;
    if (stat(local_uri, &st) < 0) {
        perror("[WARN] No file found matching URI.\n");
        handle_404(asock);
        return;
    }

    int fd = open(local_uri, O_RDONLY);
    if (fd < 0) {
        perror("[ERR] Failed to open file.\n");
        handle_500(asock);
        return;
    }

    int ct_len = st.st_size;
    char ct_type[40];
    int cnt;

    if(!strcmp(safe_uri, "/data.html")){
        while (mongoc_cursor_next (cursor, &doc)) {
            char *str;
            str = bson_as_json (doc, NULL);
            if(strlen(str) > 0){
                find_mime(ct_type, local_uri);
                fill_header(header, 200, strlen(str), ct_type);
                write(asock, header, strlen(header));
                write(asock, str, strlen(str));
            }
            bson_free (str);
        }
    }
    else{
        find_mime(ct_type, local_uri);
        fill_header(header, 200, ct_len, ct_type);
        write(asock, header, strlen(header));
        while ((cnt = read(fd, buf, BUF_SIZE)) > 0)
            write(asock, buf, cnt);
    }

    bson_destroy (query);
    mongoc_cursor_destroy (cursor);
    mongoc_collection_destroy (collection);
    mongoc_client_destroy (client);
    mongoc_cleanup ();
}
```

기존에 사용했던 서버 코드에서 main 함수를 run_server로 변경하고 http_handler 부분만 수정했다.

```c
mongoc_client_t *client;
mongoc_collection_t *collection;
mongoc_cursor_t *cursor;
const bson_t *doc;
bson_t *query;

mongoc_init ();

client = mongoc_client_new ("mongodb://localhost:27017");
collection = mongoc_client_get_collection (client, "lotto", "lotto");
query = bson_new ();
cursor = mongoc_collection_find_with_opts (collection, query, NULL, NULL);

if(!strcmp(safe_uri, "/data.html")){
	while (mongoc_cursor_next (cursor, &doc)) {
	  char *str;
    str = bson_as_json (doc, NULL);
    if(strlen(str) > 0){
	    find_mime(ct_type, local_uri);
      fill_header(header, 200, strlen(str), ct_type);
      write(asock, header, strlen(header));
      write(asock, str, strlen(str));
    }
    bson_free (str);
	}
}
```

수정된 부분인데 MongoDB와 연결하고 데이터를 가져오는 부분이다.

str에 json형태의 데이터가 저장이 되고 data.html에 헤더의 길이를 str의 길이 만큼 설정한 후 바디 부분에 str을 작성해줬다.

## 서버에서 파이썬 프로그램 실행하기

```c
//runpy.h
void runpy();
```

```c
//runpy.c
#include <stdio.h>
#include <stdlib.h>

#define SHELLSCRIPT "\
#/bin/bash \n\
python3.7 /home/pi/C-Server/env/update.py \n\
"

void runpy()
{
    system(SHELLSCRIPT);
}
```

SHELLSCRIPT에 작성한 bash 코드를 실행해주는 코드이다.

## 멀티 프로세스 사용

```c
//http.c
#include "./runpy.h"
#include "./server.h"
#include <unistd.h>

int main() {
    pid_t pid = fork();
    if(pid == 0){
        run_server();
    }
    else{
        runpy();
    }
    return 0;
}
```

서버와 크롤링하는 프로그램 모두 무한 루프를 돌기 때문에 동시에 실행 시키려면 멀티 프로세스를 사용해야 한다.

## 컴파일

```bash
gcc -o http http.c runpy.c server.c -I/usr/local/include/libmongoc-1.0 -I/usr/local/include/libbson-1.0 -L/usr/local/lib/ -L/usr/lib64 -lmongoc-1.0 -lbson-1.0
```
