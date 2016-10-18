import wikipedia
import logging
from phpserialize import serialize

wikipedia.set_rate_limiting(rate_limit=True)

class mediaWiki:

    def __init__(self):
        pass

    def getPage(self,row):
        name=row['Name'].lower()
        tokens = set(name.split())
        try:
            return wikipedia.page(name)
        except:
            pass
        
        results = wikipedia.search(name+" "+row['City'],results=5)
        if not results: return None
        weights = [0 for i in results]
        
        for n,i in enumerate(results):
            #print("Similar suggestion for %s:%s"%(name,i))
            if  row['City'] in i:
                weights[n]+=0.3
            tokens = name.split()
            l=len(tokens)
            for j in tokens:
                weights[n]+=1/l
            if 'india' in i.lower():
                weights[n]+=0.2
                
        m=max(weights)
        if m>=1:
            r = results[weights.index(m)]
            print "Max weight guess for %s :%s"%(name,r)
            return wikipedia.page(r)  

##        
##        if not page:
##
##            suggestion=wikipedia.suggest(name)
##            if suggestion:
##                print "Suggestion for %s : %s"%(name,suggestion)
##                results = wikipedia.search(suggestion,results=3)
##            for s in results:
##                print tokens.intersection(set(s.split()))
##                if len(tokens.intersection(set(s.split())))/len(tokens)>0.6:
##                    print "Got from suggestions: %s For query: %s"%(s,name)
##                    tmp=wikipedia.page(s)
##                    if row['City'] in tmp.summary:
##                        print "Accepted page from suggestions: %s"%page.title
##                        page=tmp

        return None

    def processAll(self,rows):
        pg=0
        for row in rows:
            page = self.getPage(row)
            if page:
                pg+=1
                images = filter(lambda x: not x.endswith('svg'),page.images)
                row['wikipedia']=serialize({'page_title':page.title, 'images':images,'summary':page.summary,'content':page.content})
                
        print("Pages found on wikipedis : %d/%d"%(pg,len(rows)))
            
