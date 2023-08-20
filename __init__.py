if __name__ == '__main__':
    print("start")
    from spider_module import ComicSpider
    spider = ComicSpider.ComicSpider()
    # spider.spiderChapter()
    spider.spiderContent()
    print("end")