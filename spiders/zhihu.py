# -*- coding: utf-8 -*-
import json
from urllib import parse

import re

import scrapy


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    header = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        for url in all_urls:
            match_obj = re.match(r"(https://www.zhihu.com/question/(\d+))(/|$)",url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.header, callback=self.parse_question)

    def parse_question(self,response):
        pass





    def start_requests(self):
        return [scrapy.Request("https://www.zhihu.com/#signin",callback=self.login,headers=self.header)]


    def login(self,response):
        response_text = response.text
        match_obj = re.match(r'.* value="(.*?)"', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = match_obj.group(1)
        if xsrf:
            post_url = 'https://www.zhihu.com/login/phone_num'
            post_data = {
                'xsrf':xsrf,
                'password':'wang123.',
                'phone_num':'18389796580',
                'captcha':'',
            }
            import time
            t = str(int(time.time() * 1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            yield scrapy.Request(captcha_url,headers=self.header,meta={"post_data":post_data},callback=self.login_after_captcha)


    def login_after_captcha(self,response):

        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()
        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
        except:
            print("Image open wrong")

        captcha = input("input captcha \n >")

        post_data = response.meta.get('post_data',{})
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data['captcha'] = captcha
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.header,
            callback=self.check_login,
        )]

    def check_login(self,response):
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)

