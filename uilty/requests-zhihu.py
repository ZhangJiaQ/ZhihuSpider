import re
import requests
import http.cookiejar as cooklib

agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
header = {
    'HOST':'www.zhihu.com',
    'Referer':'https://www.zhihu.com',
    'User-Agent':agent
}
session = requests.session()
session.cookies = cooklib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discared=True)
except:
    print("cookies wrong")


def is_login():
    # 通过个人中心页面返回状态码来判断是否为登录状态
    setting_url = "https://www.zhihu.com/inbox"
    response = session.get(setting_url,headers=header,allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_captcha():
    import time
    t = str(int(time.time()*1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    t = session.get(captcha_url,headers=header)
    with open("captcha.jpg","wb") as f:
        f.write(t.content)
        f.close()
    from PIL import Image
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print ("Image open wrong")

    captcha = input("input captcha \n >")
    return captcha


def get_xsrf():
    # 获取xsrf code
    response = session.get('https://www.zhihu.com',headers=header)
    re_text = response.text
    re_obj = re.match(r'.* value="(.*?)"',re_text,re.DOTALL)
    return (re_obj.group(1))


def get_index():
    response = session.get("https://www.zhihu.com",headers=header)
    with open("index_page.html","wb") as f:
        f.write(response.text.encode("utf-8"))
    print("OK")

def zhihu_login(account,password):

    if re.match(r'1\d{10}',account):
        #
        print ('phone login')
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = {
            'xsrf':get_xsrf(),
            'password':password,
            'phone_num':account,
            'captcha':get_captcha(),
        }
    elif "@" in account:
        # 判断用户名是否为邮箱
        print('mail login')
        post_url = 'https://www.zhihu.com/login/email'
        post_data = {
            'xsrf': get_xsrf(),
            'password': password,
            'phone_num': account,
            'captcha':get_captcha(),
        }
    response_text = session.post(post_url,data=post_data,headers=header)
    session.cookies.save()

#
# zhihu_login("182*******5","z*******zz")# account and password
# print(is_login())
# get_index()

get_xsrf()