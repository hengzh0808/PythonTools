import json
import os
import requests
import time
import shutil
import threading
import PyPDF2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors, styles
from reportlab.lib.units import inch
from reportlab.platypus.doctemplate import SimpleDocTemplate, PageBreak
from reportlab.platypus.flowables import PageBreak, Spacer
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from concurrent.futures import ThreadPoolExecutor

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
        # chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument("--disable-images")
        # chrome_options.add_argument("--disable-javascript")
        # driver = webdriver.Chrome(options=chrome_options)
        # print("开始爬取")
        # with open("spider_module/chapter.txt", "r") as file:
        #     lines = file.readlines()
        #     for idx, line in enumerate(lines):
        #         start_time = time.time()
        #         href = line.strip()
        #         print(f"爬取href: {href}")
        #         name, image_links = self._spider_image_links(driver, href)
        #         self._save_image_links(name, image_links)
        #         end_time = time.time()
        #         elapsed_time = end_time - start_time
        #         print(f"爬取href: {href} 完成， 耗时：{elapsed_time}")
        # print("结束爬取")

        print("开始下载图片")
        requests.adapters.DEFAULT_RETRIES = 5 # 增加重连次数
        session = requests.session()
        session.keep_alive = False # 关闭多余连接
        with open(f'spider_module/一人之下/image_links.json', "r") as json_file:
            image_links = json.load(json_file)  # 将JSON文件内容解析为Python对象
            for idx in range(421, len(image_links)):
                image_link = image_links[idx]
                name = image_link["name"]
                links = image_link["links"]
                self._download_imgs(links, f"{idx}_{name}", session)
                print(f"下载图片完成 item {idx+1} of {len(image_links)}")
        print("结束下载图片")

        # print("开始生成pdf")
        # folder_path = "spider_module/一人之下/Image"
        # # 获取文件夹下的所有文件和子文件夹
        # items = os.listdir(folder_path)
        # # 筛选出子文件夹
        # subfolders = [item for item in items if os.path.isdir(os.path.join(folder_path, item))]
        # for subfolder in subfolders:
        #     subfolder_path = f"{folder_path}/{subfolder}"
        #     image_paths = os.listdir(subfolder_path)
        #     image_paths = sorted(image_paths, key=lambda x: os.path.getctime(os.path.join(subfolder_path, x)))
        #     image_paths = [os.path.join(subfolder_path, image_path) for image_path in image_paths if not os.path.isdir(os.path.join(subfolder_path, image_path))]
        #     self._create_pdf(image_paths, subfolder)
        # print("结束生成pdf")

        # print("结束拼接pdf")
        # self._combine_pdfs()
        # print("结束拼接pdf")

    def _spider_image_links(self, driver, href):
        driver.get(href)

        name = driver.find_element(By.XPATH, "//div[@class='gb-inside-container']/h1").text
        name = name if name != None else "默认值"
        name = name.removeprefix("一人之下-")

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

    def _save_image_links(self, name, links):
        path = f'spider_module/一人之下/image_links.json'
        with open(path, 'r+', encoding='utf-8') as json_file:
            image_links = json.load(json_file)  # 将JSON文件内容解析为Python对象
            image_links.append({
                "name": name,
                "links": links
            })
            json_file.seek(0)  # 将文件指针移动到文件开头
            json.dump(image_links, json_file, indent=4, ensure_ascii=False)  # 进行覆盖写入


    log_lock = threading.Lock()
    def _download_imgs(self, image_links, folder_name, session):
        def _download_image(url, idx, folder):
            response = session.get(url, stream=True)
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

        if session:
            for idx, url in enumerate(image_links):
                image_path = _download_image(url, idx, folder)
                image_paths.append(image_path)
        else:
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
        output_path = "spider_module/一人之下/一人之下.pdf"

        # 获取目录中的所有PDF文件
        pdf_paths = [os.path.join(input_directory, file) for file in os.listdir(input_directory) if file.endswith(".pdf")]

        merger = PyPDF2.PdfMerger()

        toc = PyPDF2.PdfWriter()

        # Add individual PDFs
        for pdf_path in pdf_paths:
            pdf = PyPDF2.PdfReader(pdf_path)

            # Add the entire PDF to the merger
            merger.append(pdf)

            # Create a title page for the TOC entry
            title_page = PyPDF2.PageObject.create_blank_page(width=100, height=100)
            title_page.merge_page(pdf.pages[0])  # Assuming the first page is the title page

            # Add an entry to the TOC
            toc.add_outline_item(pdf_path, title_page)

        # Write the merged PDF with TOC to the output file
        with open(output_path, "wb") as output_file:
            merger.write(output_file)
            toc.write(output_file)

    def _create_folder_ifNeed(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
