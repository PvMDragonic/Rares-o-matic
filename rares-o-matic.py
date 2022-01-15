from datetime import datetime
from threading import Thread
from lxml import html
import xlsxwriter
import requests
import sys
import os

processed_data = []

def extract_date(string):
    string = string.replace("\n","")
    string = string[:20] if len(string) > 22 else string
    string = string.split(" ")

    string[0] = string[0].split("-")
    string[0][0], string[0][2] = string[0][2], string[0][0]
    string[0][1] = {
        "Jan" : "01", "Feb" : "02", "Mar" : "03", "Apr" : "04",
        "May" : "05", "Jun" : "06", "Jul" : "07", "Aug" : "08",
        "Sep" : "09", "Oct" : "10", "Nov" : "11", "Dec" : "12",
    }.get(string[0][1])

    return datetime.fromisoformat(
        f'{string[0][0]}-{string[0][1]}-{string[0][2]} {string[1]}')

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

            for index, msg in enumerate(posts):
                if not any(("hat" in msg, len(msg) < 100)):
                    continue

                words = str(msg.encode(sys.stdout.encoding, errors='replace'))
                words = words[2:].replace(". ", " ")
                words = words[:-1].split(" ")
                price = ""
                item = ""

                for word in words:
                    if any((word == "", ('/' in word and not '//' in word))):
                        continue

                    try:
                        w = word.lower()
                        if w[-1] == 'm':
                            if price == "":
                                if w[:-1].isdigit():
                                    price = ''.join(ch for ch in w if (ch.isdigit() or ch == '.')) + 'M'
                        elif w[-1] == 'b': 
                            if price == "":
                                if w[:-1].isdigit():
                                    price = ''.join(ch for ch in w if (ch.isdigit() or ch == '.')) + 'B'
                        elif w.isdigit():
                            if price == "":
                                if len(w) > 2:
                                    if float(w) > 200:
                                        price = w + 'M'
                                    else:
                                        price = w + 'B'
                        elif ',' in w or w[0].isdigit():
                            if price == "":
                                try:
                                    price = ''.join(ch for ch in w if (ch.isdigit() or ch == '.'))
                                    if price.count(".") > 1:
                                        price = ''.join(ch for ch in w if ch.isdigit())
                                    if 200 < float(price) < 99999:
                                        price = price + 'M'
                                    elif 200 > float(price):
                                        price = price + 'B'
                                    else:
                                        price = str(round(float(price) / 1000000, 1)) + 'M'
                                except ValueError:
                                    pass
                        elif w == 'max':
                            if price == "":
                                price = '&&&'
                        elif w == 'cash' and price == '&&&':
                            price = '2147M'
                        else:
                            if item == "": 
                                if "yellow" in w:
                                    item = "Yellow Partyhat"
                                elif "red" in w:
                                    item = "Red Partyhat"
                                elif "blue" in w:
                                    item = "Blue Partyhat"
                                elif "green" in w:
                                    item = "Green Partyhat"
                                elif "purple" in w:
                                    item = "Purple Partyhat"
                                elif "white" in w:
                                    item = "White Partyhat"
                                elif "gold" in w:
                                    item = "Golden Partyhat"
                                elif "gsh" in w:
                                    item = "Green Santa Hat"
                                elif "black" in w or "bsh" in w:
                                    item = "Black Santa Hat"
                                elif "santa" in w or "rsh" in w: 
                                    item = "Red Santa Hat"
                    except IndexError:
                        continue

                if all((item != "", price != "")):                            
                    date = extract_date(dates[index])
                    processed_data.append([item, price, date, msg])

lyra_profile_page = html.fromstring(requests.get('https://secure.runescape.com/m=forum/users.ws?searchname=Lyra&lookup=view').content)
forum_posts = [lyra_profile_page.xpath('.//section[@class="threads-list"]//article/a/@href')[i::3] for i in range(3)]

t1 = Thread(target = read_forum_page, args = (forum_posts[0], ))
t2 = Thread(target = read_forum_page, args = (forum_posts[1], ))
t3 = Thread(target = read_forum_page, args = (forum_posts[2], ))
t1.start(); t2.start(); t3.start()
t1.join(); t2.join(); t3.join()

processed_data.sort(key = lambda x : x[2], reverse = True)

for i in range(len(processed_data)):
    processed_data[i][2] = processed_data[i][2].strftime("%m/%d/%Y %H:%M:%S")

name = f'Rares {datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.xlsx'
workbook = xlsxwriter.Workbook(os.path.expanduser(f"~/Desktop/{name}"))
worksheet1 = workbook.add_worksheet()
worksheet1.set_column(0, 0, 17)
worksheet1.set_column(1, 1, 10)
worksheet1.set_column(2, 2, 20)
worksheet1.set_column(3, 3, 90)
worksheet1.set_default_row(20)

for i in range(len(processed_data)):
    worksheet1.write(f'A{i+1}', processed_data[i][0])
    worksheet1.write(f'B{i+1}', processed_data[i][1])
    worksheet1.write(f'C{i+1}', processed_data[i][2])
    worksheet1.write(f'D{i+1}', processed_data[i][3])

workbook.close()