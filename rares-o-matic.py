from threading import Thread
from lxml import html
import requests

processed_data = []

def read_forum_page(lst):
    for link in lst:
        forum_thread = html.fromstring(requests.get(f'https://secure.runescape.com/m=forum/{link}').content)
        size = int(forum_thread.xpath('.//div[@class="paging"]//ul//li//a/text()')[-1])

        if size == 1:
            continue

        for number in range(size):
            page = html.fromstring(requests.get(f'https://secure.runescape.com/m=forum/{link},goto,{number}').content)
            posts = [tag.text_content() for tag in page.xpath('.//span[@class="forum-post__body"]')]
            dates = [tag.text_content() for tag in page.xpath('.//div[@class="forum-post__message-container"]/p')]

            for msg in posts:
                if not any(("hat" in msg, len(msg) < 100)):
                    continue

                processed_data.append(msg)

lyra_profile_page = html.fromstring(requests.get('https://secure.runescape.com/m=forum/users.ws?searchname=Lyra&lookup=view').content)
forum_posts = [lyra_profile_page.xpath('.//section[@class="threads-list"]//article/a/@href')[i::3] for i in range(3)]

t1 = Thread(target = read_forum_page, args = (forum_posts[0], ))
t2 = Thread(target = read_forum_page, args = (forum_posts[1], ))
t3 = Thread(target = read_forum_page, args = (forum_posts[2], ))
t1.start(); t2.start(); t3.start()
t1.join(); t2.join(); t3.join()