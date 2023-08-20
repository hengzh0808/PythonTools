import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import requests
from PIL import Image
from reportlab.pdfgen import canvas
import time
import shutil
from concurrent.futures import ThreadPoolExecutor
import threading
from PyPDF2 import PdfFileReader, PdfFileWriter

class ComicSpider:
    def __int__(self):
        pass
    
    def spiderChapter(self):
        from bs4 import BeautifulSoup

        # 读取本地HTML文件
        with open("spider_module/一人之下-漫画屋.html", "r", encoding="utf-8") as file:
            content = file.read()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(content, "html.parser")

        # 使用XPath选择器提取内容和href
        # links = soup.select("/html//a[@class='j-chapter-link']")
        links = soup.select("a.j-chapter-link")

        # 创建字典来存储内容和href
        data = []

        # 遍历所有选中的<a>标签
        for link in links:
            content = link.text.strip()
            href = link["href"]

            chapter = {}
            chapter['name'] = content
            chapter['href'] = href

            data.append(chapter)

        # 输出JSON形式
        output_json = json.dumps(data, indent=4, ensure_ascii=False)
        # 写入新文件
        with open("spider_module/chapter.json", "w") as output_file:
            json.dump(output_json, output_file, indent=4)


    def spiderContent(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")

        driver = webdriver.Chrome(options=chrome_options)

        print("开始爬取")
        with open("spider_module/chapter.txt", "r") as file:
            lines = file.readlines()
            for idx, line in enumerate(lines):
                start_time = time.time()
                href = line.strip()
                print(f"爬取href: {href}")
                name, image_links = self._spider_image_links(driver, href)
                image_paths = self._download_imgs(image_links, href, name)
                self._create_pdf(image_paths, f"{idx}_{name}")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"爬取href: {href} 完成， 耗时：{elapsed_time}")



        print("结束爬取")

    def _spider_image_links(self, driver, href):
        driver.get(href)

        name = driver.find_element(By.XPATH, "//div[@class='gb-inside-container']/h1").text
        name = name if name != None else "默认值"
        xpath_to_wait = "//div[@class='gb-inside-container']/img"
        wait = WebDriverWait(driver, 10)  # 最多等待10秒
        elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_to_wait)))

        image_links = []
        for element in elements:
            src = element.get_attribute("data-src")
            data_src = element.get_attribute("data-src")
            if src == None:
                src = element.get_attribute('src')
            if src == None:
                html = element.get_attribute("outerHTML")
                print(f"爬取href: {href}, name: {name}，获取src失败 outerHTML: {html}")
                raise ValueError("Division by zero is not allowed")
            else:
                image_links.append(src)

        return name, image_links

    log_lock = threading.Lock()
    def _download_imgs(self, image_links, href, folder_name):
        def _download_image(url, idx, folder):
            response = requests.get(url, stream=True)
            image_path = os.path.join(folder, f"{idx}.jpg")

            if response.status_code == 200 and len(response.content) != 0:
                with open(image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                with self.log_lock:
                    print(f"图片下载不成功 url: {url}")
                    image_404_path = "spider_module/404.jpg"
                    shutil.copy(image_404_path, image_path)

            return image_path


        folder = f'spider_module/一人之下/Image/{folder_name}'
        self._create_folder_ifNeed(folder)
        image_paths = []
        with ThreadPoolExecutor() as executor:
            image_path_futures = []
            for idx, url in enumerate(image_links):
                future = executor.submit(_download_image, url, idx, folder)
                image_path_futures.append(future)

            for future in image_path_futures:
                image_paths.append(future.result())

        return image_paths


    def _create_pdf(self, image_paths, pdf_name):
        folder = 'spider_module/一人之下/Pdf'
        self._create_folder_ifNeed(folder)
        pdf_path = f"{folder}/{pdf_name}.pdf"
        page_width, page_height = 800, 1270
        c = canvas.Canvas(pdf_path, pagesize=(page_width, page_height))

        for image_path in image_paths:
            img = Image.open(image_path)
            c.drawImage(image_path, 0, 0, width=page_width, height=page_height)
            c.showPage()

        c.save()

    def _combine_pdfs(self):
        # 输入目录和输出PDF文件名
        input_directory = "spider_module/一人之下/Pdf"
        output_pdf = "一人之下/一人之下.pdf"

        # 获取目录中的所有PDF文件
        pdf_files = [file for file in os.listdir(input_directory) if file.endswith(".pdf")]

        # 创建PdfFileWriter对象
        output_pdf_writer = PdfFileWriter()

        # 遍历每个PDF文件，将其添加到输出PDF文件中
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_directory, pdf_file)
            pdf_reader = PdfFileReader(pdf_path)
            pdf_writer = PdfFileWriter()

            # 将子PDF的每一页添加到输出PDF的PdfFileWriter对象中
            for page_num in range(pdf_reader.getNumPages()):
                page = pdf_reader.getPage(page_num)
                pdf_writer.addPage(page)

            # 将子PDF的PdfFileWriter对象添加到输出PDF的PdfFileWriter对象中
            output_pdf_writer.addPage(pdf_writer.getPage(0))

        # 创建目录页
        table_of_contents = []
        for pdf_file in pdf_files:
            table_of_contents.append(pdf_file)

        # 将目录页添加到输出PDF的PdfFileWriter对象中
        output_pdf_writer.addBookmark("Table of Contents", 0)
        for idx, pdf_file in enumerate(table_of_contents):
            output_pdf_writer.addBookmark(pdf_file, idx + 1, parent=None)

        # 将输出PDF写入文件
        with open(output_pdf, "wb") as output_stream:
            output_pdf_writer.write(output_stream)

        print("PDFs merged successfully with table of contents.")

    def _create_folder_ifNeed(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
