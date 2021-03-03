"""his script when run will extract article links from the Finshots website
 and update the links table in database"""

import datetime
import os

import mysql.connector as mc
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# making the connection to database
load_dotenv()
User = os.getenv('USER')
Host = os.getenv('HOST')
Password = os.getenv('PASSWORD')
Database = os.getenv('DATABASE')

db = mc.connect(user=User, host=Host, password=Password, database=Database)
cur = db.cursor()

# storing links to be scrapped
URL = {
    "https://finshots.in/archive": "archive",
    "https://finshots.in/brief/": "brief",
    "https://finshots.in/markets/": "markets",
    "https://finshots.in/infographic/": "infographic"
}

# inserting data for each category
for url in URL:

    # fetching source code of the link
    r = requests.get(url).content

    soup = BeautifulSoup(r, 'html.parser')
    div = soup.find('div', class_='post-feed')
    articles = div.find_all('article')

    for item in articles:
        # scrapping the data
        article = {
            'link': "https://finshots.in" + item.find('a')['href'],
            'title': item.find('img')['alt'],
            'link_date': item.find('time')['datetime']
        }

        now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

        # updating links into articles table
        try:
            cur.execute(
                f"insert into articles values('{article['link']}',"
                f"'{article['title']}', '{URL[url]}','{article['link_date']}',"
                f"'{now}');")

            db.commit()
        except (mc.errors.IntegrityError, mc.errors.ProgrammingError):
            pass

    # deleting data that is not required
    if URL[url] == 'archive':
        # storing only the links that were updated in last 3 days for archives
        cur.execute(
            f"delete from articles where category='{URL[url]}' and"
            " timestampdiff(day, link_date, curdate())>2 ;"
        )
    else:
        # storing only last 2 links for all other links
        cur.execute(
            "delete from articles where link_date "
            "not in(select link_date from"
            "(select link_date from articles where category="
            f"'{URL[url]}' order by link_date desc limit 2)fo) "
            f" and category='{URL[url]}'"
        )

    db.commit()

print('database updated with latest articles!')

# closing connection to the database
cur.close()
db.close()
