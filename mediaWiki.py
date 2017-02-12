import wikipedia
import csv
import threading
from bs4 import BeautifulSoup
import time, sys
import requests
from fbGraph import safe_dec_enc

# FOR FINDING CORRECT WIKI URL
class Url_Finder:
    def __init__(self):
        pass

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
        except requests.exceptions.ChunkedEncodingError:
            pass

    def gracious_request(self, x, isPage):
        data = []
        start_time = 0
        while not data:
            if (time.time() - start_time) > 12:
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

    def processAll(self, rows):
        self.rows = rows

        N = len(self.rows)
        if N < 400:
            self.rows_per_thread = 10
        elif 400 < N < 1200:
            self.rows_per_thread = 20
        else:
            self.rows_per_thread = N/60

        print 'ROWS PER THREAD:', self.rows_per_thread
        self.thread_master()


# FOR EXTRACTING DATA FROM WIKI URL
class Data_Extractor:
    def __init__(self):
        self.req_fields = ['Website','Established','Location','Type','Campus','Affiliations','Principal','Motto','Academic staff']

    def get_infobox_attributes(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        infobox = soup.find('table', class_='infobox')
        key_pairs = {}
        if infobox:
            blocks = infobox.findAll('tr')
            for block in blocks:
                attr = block.find('th')
                if attr:
                    val = block.find('td')
                    if val:
                        attr = attr.text.encode('ascii','ignore').strip()
                        val = val.text.encode('ascii','ignore')
                        val = filter(lambda i: i, val.splitlines())
                        if len(val):
                            key_pairs[attr] = val[0]
                        else:
                            key_pairs[attr] = ''
        return key_pairs

    def symlink_cleaner(self, data, ext=False):
        start = ['[']
        end = [']']
        if ext:
            start.append('(')
            end.append(')')
        symlink = False
        cleaned = ''
        for _ in data:
            if _ in start and not symlink:
                symlink = True
            if not symlink:
                cleaned += _
            if _ in end and symlink:
                symlink = False
        return cleaned.strip()

    def established_cleaner(self, data):
        if not data:
            return ''

        data = data.split(';')
        if len(data) > 1:
            return data[0]
        else:
            data = data[0]
        return self.symlink_cleaner(data, True)

    def website_cleaner(self, data):
        if not data:
            return ''

        if len(data) <= 5:
            return None
        return self.symlink_cleaner(data)

    def master_cleaner(self, attributes):
        if 'Website' in attributes:
            attributes['Website'] =  self.website_cleaner(attributes['Website'])
        if 'Established' in attributes:
            attributes['Established'] = self.established_cleaner(attributes['Established'])
        if 'Affiliations' in attributes:
            attributes['Affiliations'] = self.symlink_cleaner(attributes['Affiliations'])
        if 'Principal' in attributes:
            attributes['Principal'] = self.symlink_cleaner(attributes['Principal'])

        for key in attributes.keys():
            if attributes[key]:
                attributes[key] = attributes[key].strip()

    def extract_from_wikipedia(self, row):
        html = requests.get(row['wikipedia_url'])
        attributes = self.get_infobox_attributes(html.text)
        self.master_cleaner(attributes)
        for field in self.req_fields:
            if attributes.get(field):
                row[field] = attributes[field]

    def processAll(self, rows):
        hits = 0
        for row in rows:
            if row['wikipedia_url']:
                self.extract_from_wikipedia(row)
                hits += 1
        return hits

class mediaWiki:
    def __init__(self):
        pass

    def processAll(self, rows):
        print '\nFETCHING DATA FROM WIKIPEDIA'
        find = Url_Finder()
        find.processAll(rows)

        print '\nUPDATING DATA FROM WIKIPEDIA'
        extract = Data_Extractor()
        hits = extract.processAll(rows)
        print 'TOTAL HITS:', hits
