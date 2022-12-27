#%%
import time
import math
import logging
import requests
from datetime import datetime
from pymongo import MongoClient
#%%
# set filename by datetime
filename = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
log_path = 'log/{filename}.log'.format(filename=filename)
# set up logging to file 
logging.basicConfig( 
    filename=log_path,
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'
)

#%%
# 確認該關鍵字的頁數
def check_page(text: str, items_count=300):
    url = 'https://ecshweb.pchome.com.tw/search/v3.3/all/' \
          f'results?q={text}&page=1&sort=sale/dc'
    a = requests.get(url)
    data = a.json()
    # 每一頁共幾筆資料
    page_of_items = len(data['prods'])    
    # 需要300筆，共要爬幾頁
    pages = math.ceil(items_count/page_of_items)

    # 如果該關鍵字 尚未有300筆資料，則取最大頁數
    if pages > data['totalPage'] :
        pages = data['totalPage']
        logging.info(f'關鍵字:{text}未有300筆資料')
    return pages

# 爬蟲主程式
def crawler(text: str, pages: int):
    web_list = list()
    # 爬取各頁數
    for page in range(1, pages):
        logging.info(f'==  第{page}頁 ==') 
        url = 'https://ecshweb.pchome.com.tw/search/v3.3/all/' \
            f'results?q={text}&page={page}&sort=sale/dc'
        a = requests.get(url)
        data = a.json()
        time.sleep(0.1)
        # 如果資料存在
        if data:
            try:
                pageData = data['prods']
                count = len(pageData)
                logging.info(f'商品數量：{count}')
                web_list.extend(pageData)
            except Exception as e:
                logging.exception(f'獲取失敗: {e}')
        else:
            logging.error(f'獲取資料失敗')
    ## 補創立、修改時間
    update = {
        "channel":'pchome',
        "created_at": datetime.now(),
        "modified_at": datetime.now()
    }
    all_list = list({**item,**update} for item in web_list)
    
    return all_list

# 存進db
def insert_db(data: list):
    client = MongoClient(
        host='localhost:27017', 
        username='admin', 
        password='123456'
    )
    db = client['Web']['Test']
    try:
        db.insert_many(data)
        logging.info('儲存成功')
    except Exception as e:
        logging.exception(f'儲存失敗: {e}')
    return 

#%%
if __name__ == '__main__':
    text = '洗衣精'

    logging.info(f'==開始檢查頁數==')
    pages = check_page(text=text)
    logging.info(f'==完成檢查頁數，共{pages}頁==')
    
    logging.info(f'==查詢關鍵字：{text}==')
    data = crawler(text=text, pages=pages)
    logging.info('==完成爬取資料==')
    
    logging.info('==開始儲存==')
    insert_db(data)
    logging.info('==完成儲存==')
# %%
