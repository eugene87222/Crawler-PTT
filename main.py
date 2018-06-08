import PTTCrawler
import time

def main():
    ans = input('Want to update board_list.txt? [yes/no]:')
    if ans.lower() == 'yes':
        BOARD_LIST = PTTCrawler.GetBoardList('https://www.ptt.cc/bbs/hotboards.html')
    elif ans.lower() == 'no':
        BOARD_LIST = PTTCrawler.ReadBoardList()

    BOARD = input('Which board would you want to crawl? (see board_list.txt):').lstrip().rstrip()
    BOARD_URL = '/bbs/' + BOARD + '/'

    # if no input or the input board is not in board_list.txt
    if BOARD == '' or BOARD not in BOARD_LIST:
        print ('EXIT')
    else:
        total_page_num = PTTCrawler.GetTotalPageNum(BOARD_URL)
        print (u'Board <{}> has {} pages in total.'.format(BOARD, total_page_num))

        page_want_to_crawl = input(u'How many pages do you want to crawl? ')

        # if the input is valid (negative number, string, input nothing)
        if page_want_to_crawl == '' or not page_want_to_crawl.isdigit() or int(page_want_to_crawl) <= 0:
            print ('EXIT')
        else:
            page_want_to_crawl = min(int(page_want_to_crawl), total_page_num)

            pages_link = list()
            for i in range(total_page_num, total_page_num - page_want_to_crawl, -1):
                link = BOARD_URL + 'index' + str(i) + '.html'
                pages_link.append(link)
            
            start = time.time()

            posts = PTTCrawler.GetPosts(pages_link)
            posts_data = PTTCrawler.GetArticles(posts)
                
            if len(posts) == len(posts_data):
                print (u'Finish. {} pages\n{} posts in total'.format(page_want_to_crawl, len(posts)))
            else:
                print (u'There must be something wrong.\nTotal posts: {}\nPosts we crawl: {}'.format(len(posts), len(posts_data)))
            
            print (u'Spend {} seconds on crawling.'.format(time.time()-start))

            ans = input('Save to database? [yes/no]:')
            if ans.lower() == 'yes':
                PTTCrawler.Save2DB('data.db', posts_data)
            ans = input('Save to excel? [yes/no]:')
            if ans.lower() == 'yes':
                PTTCrawler.Save2Excel(posts_data)
            
    print ('====================')

if __name__ == '__main__':
    main()