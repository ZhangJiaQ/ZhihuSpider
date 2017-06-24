# -*- coding: utf-8 -*-
import datetime
import json
from urllib import parse

import re

import scrapy
from scrapy.loader import ItemLoader

from items import ZhuhuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    header = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.header, callback=self.parse_question)
            else:
                # 如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url, headers=self.header, callback=self.parse)

    def parse_question(self,response):
        # 处理question页面， 从页面中提取出具体的question item
        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
        i=1
        if match_obj:
            question_id = int(match_obj.group(2))
        else:
            match_obj = i
            i+=1

        item_loader = ItemLoader(item=ZhuhuQuestionItem(), response=response)
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_css("content", ".QuestionHeader-detail")
        item_loader.add_value("url", response.url)
        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css("answer_num", ".List-headerText span::text")
        item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.header,callback=self.parse_answer)
        yield question_item

    def parse_answer(self, reponse):
        # 处理question的answer
        ans_json = json.loads(reponse.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comments_count"]
            answer_item["creat_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.header, callback=self.parse_answer)


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

