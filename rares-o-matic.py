from datetime import datetime
from threading import Thread
from time import sleep
from lxml import html

import xlsxwriter
import requests
import os

processed_data = []
start = datetime.now()

DATES = {
    "Jan" : "01", "Feb" : "02", "Mar" : "03", "Apr" : "04",
    "May" : "05", "Jun" : "06", "Jul" : "07", "Aug" : "08",
    "Sep" : "09", "Oct" : "10", "Nov" : "11", "Dec" : "12",
}

TYPES = (
    'sold', 'bought', 'nib', 'inb', 'nis', 'ins', 'buy', 'sell'
)

NAMES = (
    'santa', 'hat', 'hween', 'h\'ween', 'ween', 'hallowe\'en', 'halloween', 'mask', 'egg', 'scythe', 
    'hw', 'phat', 'partyhat', 'party', 'cracker', 'rsh', 'gsh', 'bsh', 'wreath', 'disk', 'pumpkin'
)

COLORS = (
    'blue', 'white', 'red', 'purple', 'yellow', 'green', 'black', 'golden', 'gold'
)

class ItemInformation():
    def __init__(self) -> None:
        self.date = None
        self.type = None
        self.name = None
        self.price = None

def collect_data():
    collecting = True

    def progress_report():
        """Updates displayed info about the collected data."""
        num_of_dots = 1
        while collecting:
            os.system("cls||clear")
            print('Collecting' + num_of_dots * '.')
            print(f'\n\nElapsed time: {str(datetime.now() - start)[:-7]}')
            print(f'\nPrices collected: {len(processed_data)}')

            if num_of_dots < 3:
                num_of_dots += 1  
            else:
                num_of_dots = 1

            sleep(1)

    def read_forum_page(lst):
        def extract_date(string):
            """Gets mm/dd/yyyy from the post date text string."""
            string = string.replace("\n","")
            string = string[:20] if len(string) > 22 else string
            string = string.split(" ")
            string[0] = string[0].split("-")
            string[0][0], string[0][2] = string[0][2], string[0][0]
            string[0][1] = DATES.get(string[0][1])

            return datetime.fromisoformat(
                f'{string[0][0]}-{string[0][1]}-{string[0][2]} {string[1]}')

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
                    # Filters unwanted posts.
                    if any(["CURRENT RARE PRICES" in msg, len(msg) > 100]):
                        continue

                    # Most follow the structure of "[transaction type] [item] for [price]"".
                    post = msg.split("for")
                    if len(post) <= 1:
                        # If it differs from the above pattern, it's just easier to skip.
                        continue

                    item = ItemInformation()

                    words = [word.lower() for word in post[0].split(" ")]
                    for i, word in enumerate(words):
                        try:                                
                            if not item.type:
                                if word in TYPES:
                                    item.type = word
                                    continue

                            if not item.name:
                                if word in NAMES:
                                    item.name = word

                                    if item.name in ("hat", "mask"):
                                        second_name = words[i-1]
                                        item.name = f"{second_name} {item.name}" # "santa hat".
                                        third_name = words[i-2]
                                        if third_name in COLORS:
                                            item.name = f"{third_name} {item.name}" # "red santa hat".
                                    elif item.name in ("party", "santa"):
                                        second_name = words[i-1]
                                        if second_name in COLORS:
                                            item.name = f"{second_name} {item.name}" # "red party".
                                        item.name = f"{item.name} hat" # "red party hat".
                                    elif item.name in ("partyhat", "phat"):
                                        second_name = words[i-1]
                                        if second_name in COLORS:
                                            item.name = f"{second_name} {item.name}" # "red partyhat".
                                    elif item.name in ("hw", "hween", "h'ween", "ween", "halloween", "hallowe\'en"):
                                        second_name = words[i-1]
                                        if second_name in COLORS:
                                            item.name = f"{second_name} {item.name}" # "red hween".
                                        item.name = f"{item.name} mask" # "red hween mask".
                                    elif item.name in ("egg", "scythe", "wreath"):
                                        second_name = words[i-1]
                                        item.name = f"{second_name} {item.name}" # "easter egg"; "christmas scythe".
                                    elif item.name == "disk":
                                        item.name = "disk of returning"
                        except Exception:
                            pass
                           
                    if all([item.name, item.type]):
                        item.date = extract_date(dates[index])
                        item.price = post[1].split("https")[0] # Some posts have an imgur link attached after the price.
                        processed_data.append(item)

    lyra_profile_page = html.fromstring(requests.get('https://secure.runescape.com/m=forum/users.ws?searchname=Lyra&lookup=view').content)
    forum_posts = [lyra_profile_page.xpath('.//section[@class="threads-list"]//article/a/@href')[i::3] for i in range(3)]

    Thread(target = progress_report).start()
    t1 = Thread(target = read_forum_page, args = (forum_posts[0], ))
    t2 = Thread(target = read_forum_page, args = (forum_posts[1], ))
    t3 = Thread(target = read_forum_page, args = (forum_posts[2], ))
    t1.start(); t2.start(); t3.start()
    t1.join(); t2.join(); t3.join()
    collecting = False # Breaks progress_report's thread.

def save_data():
    processed_data.sort(key = lambda x : x.date, reverse = True)

    for i in range(len(processed_data)):
        processed_data[i].date = processed_data[i].date.strftime("%Y-%m-%d %H:%M:%S")

    name = f'Rares {datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.xlsx'
    workbook = xlsxwriter.Workbook(os.path.expanduser(f"~/Desktop/{name}"))
    worksheet1 = workbook.add_worksheet()
    worksheet1.set_column(0, 0, 20)
    worksheet1.set_column(1, 1, 10)
    worksheet1.set_column(2, 2, 20)
    worksheet1.set_column(3, 3, 60)
    worksheet1.set_column(4, 4, 90)
    worksheet1.set_default_row(30)

    for i in range(len(processed_data)):
        worksheet1.write(f'A{i+1}', processed_data[i].date)
        worksheet1.write(f'B{i+1}', processed_data[i].type)
        worksheet1.write(f'C{i+1}', processed_data[i].name)
        worksheet1.write(f'D{i+1}', processed_data[i].price)

    workbook.close()
    os.system("cls||clear")

collect_data()
save_data()
input(
    print(
        f'Elapsed time: {datetime.now() - start}\nFile saved to {os.path.expanduser(f"~/Desktop")}.'
    )
)