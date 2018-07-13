from bs4 import BeautifulSoup
from urllib.request import urlopen

def createDriver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')

    capa = DesiredCapabilities.CHROME
    capa['pageLoadStrategy'] = 'none'
    driver = webdriver.Chrome(chrome_options=chrome_options, desired_capabilities=capa)
    return driver

if __name__ == '__main__':

    # 一人之下漫画

    # 所有章节
    response = urlopen("http://www.omanhua.com/comic/17521/")
    content = response.read()
    soup = BeautifulSoup(content,'html.parser')
    sections = soup.find('div', attrs={'class':'subBookList'}).find_all('a')
    sections.reverse()

    # 创建浏览器


    # 加载界面
    for section in sections:
        # 加载分页
        # http://www.omanhua.com/comic/17521/256085/index.html
        url = "http://www.omanhua.com" + section.attrs["href"] + "index.html"

        # 统计分页数量
        driver = createDriver()
        driver.get(url)
        page_count = 0
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//select[@id="pageSelect"]/option'))
            )
            page_count = len(driver.find_elements_by_xpath('//select[@id="pageSelect"]/option'))
        except Exception as error:
            pass
        finally:
            driver.close()

        # 统计本话的图片
        current_page = 1
        while current_page <= page_count:
            url = "http://www.omanhua.com" + section.attrs["href"] + "index.html?p=" + str(current_page)
            import datetime
            begin = datetime.datetime.now()
            driver = createDriver()
            driver.get(url)
            try:
                # element = driver.find_element_by_id('imgPreLoad')
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@id="mangaBox"]/img[@id="mangaFile"]'))
                )
                element = driver.find_element_by_xpath('//div[@id="mangaBox"]/img[@id="mangaFile"]')
                imgurl = element.get_attribute('src')

                end = datetime.datetime.now()
                index = sections.index(section) + 1
                print('耗时:' + str((end-begin).seconds) + '  第' + str(index) + '话，第' + str(current_page) + '页：' + imgurl)
            except BaseException as error:
                pass
            finally:
                current_page = current_page+1
                driver.close()
    pass