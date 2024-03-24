from module.crawler import Crawler

'''
100 : 정치
101 : 경제
102 : 사회
103 : 생활/문화
104 : 세계
105 : IT/과학
'''

if __name__ == "__main__":
    crawler = Crawler("https://news.naver.com/section/", ["100", "101", "102", "103", "104", "105"])
    
    crawler.crawl()