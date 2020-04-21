import warnings
warnings.filterwarnings('ignore')

import sqlite3
import requests
from pandas import DataFrame
from bs4 import BeautifulSoup
import multiprocessing
from multiprocessing import Pool

cpu = multiprocessing.cpu_count()


##########################################
# get the html code with given url       #
# param: url -> url of the web page      #
##########################################
def get_page_content(url):
    res = requests.get(
        url=url,
        cookies={'over18': '1'}
    )
    content = BeautifulSoup(res.text)

    return content


#####################################################
# get the page number of the board (e.g. Gossiping) #
# param: BOARD_URL -> url of the board              #
#####################################################
def get_total_pagenum(BOARD_URL):
    soup = get_page_content('https://www.ptt.cc' + BOARD_URL + 'index.html')

    next_page = soup.find('div', 'btn-group-paging').find_all('a', 'btn')
    next_link = next_page[1].get('href')

    total_page = next_link.lower().replace(BOARD_URL + 'index', '')
    total_page = int(total_page[:-5]) + 1
    
    return total_page


#####################################################
# get the list of all boards and save as a txt file #
# param: url -> url of the board list page          #
# see board_list.txt                                #
#####################################################
def get_board_list(url):
    content = get_page_content(url)
    content = content.findAll('div', {'class':'board-name'})

    board_list = list()

    file = open('board_list.txt', 'w', encoding='utf-8')

    for i in content:
        board_list.append(i.text.lower())
        file.write(i.text.lower()+'\n')

    file.close()

    return board_list


###############################################
# read the list of all boards from a txt file #
# see board_list.txt                          #
###############################################
def read_board_list():
    file = open('board_list.txt', 'r', encoding='utf-8')

    board_list = list()
    for line in file:
        board_list.append(line.strip().lower())

    file.close()

    return board_list


######################################################
# get the meta data of each post in a post list page #
# param: link -> url of post list page               #
######################################################
def parse_metadata(link):
    url = 'https://www.ptt.cc' + link
    soup = get_page_content(url)
    
    articles = soup.find_all('div', 'r-ent')
    
    posts = list()
    
    for article in articles:
        meta = article.find('div', 'title').find('a')
        if meta:
            posts.append({
                'link': meta.get('href'),
                'title': meta.get_text(),
                'date': article.find('div', 'date').get_text(),
                'author': article.find('div', 'author').get_text(),
                'push': article.find('div', 'nrec').get_text()
            })
    
    return posts


#######################################################
# get the meta data of all the posts                  #
# param: pages_link -> url of post list page (a list) #
#######################################################
def get_posts(pages_link):
    with Pool(cpu) as p:
        post_list = p.map(parse_metadata, pages_link)
    
    all_post_list = list()
    
    for each_page in post_list:
        for each_post in each_page:
            all_post_list.append(each_post)
    
    return all_post_list


##################################
# get the article of the post    #
# param: link -> url of the post #
##################################
def parse_article(link):
    content = get_page_content('https://www.ptt.cc' + link)
    
    shift = content.findAll('div',['article-metaline', 'article-metaline-right', 'push'])
    if shift:
        for elem in shift:
            elem = elem.extract()
    
    main_content = content.find(id='main-content')
    if main_content:
        content = main_content.text.lstrip().rstrip()
    else:
        content = 'None'
    
    return content


#########################################
# get the articles of each post         #
# param: post_link -> urls of all posts #
#########################################
def get_articles(post_list):
    post_link = [entry['link'] for entry in post_list]

    all_post_content = list()

    with Pool(cpu) as p:
        contents = p.map(parse_article, post_link)
    
    for i in range(len(post_list)):
        all_post_content.append({
            'title': post_list[i]['title'],
            'link': post_list[i]['link'],
            'date': post_list[i]['date'],
            'author': post_list[i]['author'],
            'push': post_list[i]['push'],
            'content': contents[i]
        })

    return all_post_content


##########################################
# save data into SQLite database         #
# param: db_name -> name of the database #
#        posts -> posts data             #
##########################################
def save_to_db(db_name, posts):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    create_table = """ CREATE TABLE IF NOT EXISTS table1(
                        ID integer PRIMARY KEY,
                        title text NOT NULL,
                        link text NOT NULL,
                        date text NOT NULL,
                        author text NOT NULL,
                        push text NOT NULL,
                        content text NOT NULL
                        ); """
    cur.execute(create_table)
    for i in posts:
        cur.execute("insert into table1 (title, link, date, author, push, content) values (?, ?, ?, ?, ?, ?)",
            (i['title'], i['link'], i['date'], i['author'], i['push'], i['content']))
    conn.commit()
    conn.close()


##############################
# save data into excel       #
# param: posts -> posts data #
##############################
def save_to_excel(posts):
    titles = [entry['title'] for entry in posts]
    links = [entry['link'] for entry in posts]
    dates = [entry['date'] for entry in posts]
    authors = [entry['author'] for entry in posts]
    pushes = [entry['push'] for entry in posts]
    contents = [entry['content'] for entry in posts]
    df = DataFrame({
        'title':titles,
        'link':links,
        'date': dates,
        'author':authors,
        'push': pushes,
        'content': contents
        })
    df.to_excel('data.xlsx', sheet_name='sheet1', index=False, columns=['title', 'link', 'date', 'author', 'push', 'content'])
