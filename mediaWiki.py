import wikipedia
import csv
import threading
from bs4 import BeautifulSoup
import time, sys
import requests
from fbGraph import safe_dec_enc

class mediaWiki:
    def __init__(self):
        self.rows_per_thread = 20

    def get_infobox(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        infobox = soup.find('table', class_='infobox vcard')
        if infobox:
            address = infobox.find('tr', class_='adr')
            address = address if address else infobox.find('td', class_='adr')
            if address:
                return safe_dec_enc(address.text)
        return ''

    def explode(self, word):
        word = word.lower()
        separators=[' ',',','/','-']
        split=[]
        new=False
        tmp=""
        for i in word:
            if i in separators:
                new = True
                continue
            elif new:
                if len(tmp) > 1:
                    split.append(tmp)
                tmp = ""
                new = False
            tmp+=i
        if tmp:
            split.append(tmp)

        stop_words = ['institute','college','university','classes','class','of','&','and','at']
        split = filter(lambda x: not x in stop_words, split)
        return set(split)

    def content_validate(self, tokens, page, locality, city):
        weight = 0
        tokens =  tokens | self.explode(locality)

        info_card = ''
        intro = ''
        summary = ''
        while True:
            try:
                info_card = self.get_infobox(page.html())
                intro =  safe_dec_enc(page.section('Introduction') if page.section('Introduction') else '')
                summary = safe_dec_enc(page.summary)
                break
            except requests.exceptions.ConnectionError:
                pass
        summary = summary.lower() + intro.lower() + info_card.lower()
        n = len(tokens)
        for i in tokens:
            if i in summary:
                weight += 1.0/n
        if weight >= 0.7 and city in summary:
            return True
        return False

    def title_validate(self, tokens, titles, locality, city):
        weights = [0 for i in titles]
        titles = [i.lower() for i in titles]

        for n,i in enumerate(titles):
            if city and city in i:
                weights[n] += 0.4
            for j in tokens:
                if j in i:
                    weights[n] += 0.5

        m = max(weights)
        i = weights.index(m)

        if m >= 1.0:
            page = self.gracious_request(titles[i], True)
            if page and self.content_validate(tokens, page, locality, city):
                return page
        return None

    def gracious_request_slave(self, x, isPage, data):
        try:
            if not data:
                if isPage:
                    page = wikipedia.page(x)
                    if not data:
                        data.append(page)
                else:
                    results = wikipedia.search(x ,results=5)
                    if not data:
                        data.append(results)
        except wikipedia.exceptions.PageError:
            data.append(None)
        except wikipedia.exceptions.DisambiguationError:
            data.append(None)
        except requests.exceptions.ConnectionError:
            pass

    def gracious_request(self, x, isPage):
        data = []
        start_time = 0
        while not data:
            if (time.time() - start_time) > 6:
                th1 = threading.Thread(target=self.gracious_request_slave, args=(x, isPage, data))
                th1.daemon = True
                th1.start()
                start_time = time.time()
        if data:
            return data[0]
        return None

    def getPage(self, row):
        name = safe_dec_enc(row['Name']).lower()
        locality = ''
        city = ''

        if row['Locality']:
            locality = safe_dec_enc(row['Locality']).lower()
        if row['City']:
            city = safe_dec_enc(row['City']).lower()

        tokens = self.explode(name)
        page = self.gracious_request(name, True)
        if page and self.content_validate(tokens, page, locality, city):
            return page

        results = self.gracious_request(name+" "+city, False)
        if not results:
            return None
        results = map(safe_dec_enc, results)
        return self.title_validate(tokens, results, locality, city)

    def thread_slave(self, i):
        begin = i*self.rows_per_thread
        end = (i+1)*self.rows_per_thread

        for row in self.rows[begin:end]:
            x = self.getPage(row)
            if x:
                self.hits += 1
                row['wikipedia_url'] = x.url
        print 'THREAD {0:<3} DONE. PROCESSED ROWS: {1}'.format(i+1, len(self.rows[begin:end]))

    def thread_master(self):
        n_threads = len(self.rows)/self.rows_per_thread
        if len(self.rows)%self.rows_per_thread != 0:
            n_threads += 1

        slaves = [threading.Thread(target=self.thread_slave, args=(i,), name=i) for i in range(n_threads-1)]
        slaves.append(threading.Thread(target=self.thread_slave, args=(n_threads-1 ,), name=n_threads-1))

        print "TOTAL SLAVES :", len(slaves),'\n'
        for _ in slaves:
            _.start()
        for _ in slaves:
            _.join()
        print 'TOTAL HITS:',self.hits

    def processAll(self, rows):
        print '\nFetching data from Wikipedia'

        self.hits = 0
        self.rows = rows
        if len(self.rows) < 200:
            self.rows_per_thread = 10
        if len(self.rows) > 1200:
            self.rows_per_thread = 50

        self.thread_master()
