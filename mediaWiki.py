import wikipedia
import logging
from phpserialize import serialize
from fbGraph import UTF8
import sys

wikipedia.set_rate_limiting(rate_limit=True)

class mediaWiki:

    def __init__(self):
        pass

    def explode(self,string):
        string=string.lower()
        separators=[' ',',','.','/','-']
        split=[]
        new=False
        tmp=""
        for i in string+".":
            if i in separators:
                new = True
                continue
            elif new:
                split.append(tmp)
                tmp = ""
                new = False
            tmp+=i
        if tmp:
            split.append(tmp)

        split = filter(lambda x: not x in ['institute','college','university','classes','class','of','&','and','at'],split)
        return set(split)
      
    def getPage(self,row):
        name=unicode(row['Name'])
        city=unicode(row['City'])
        tokens = self.explode(name)
        l=len(tokens)
        try:
            page = wikipedia.page(name)
            if city in page.summary.lower():
                return page
        except:
            pass
        
        results, suggestion = wikipedia.search(name+" "+city,results=5,suggestion=True)
        if not results: return None
        results= map(lambda x : x.lower(),results)
        weights = [0 for i in results]
        
        for n,i in enumerate(results):
            #print("Similar suggestion for %s:%s"%(name,i))
            if  city in i:
                weights[n]+=0.6
            for j in tokens:
                if j in i:
                    weights[n]+=1.0/l
            if 'india' in i.lower():
                weights[n]+=0.3
                
        m=max(weights)
        i=weights.index(m)
        if m>=1.2 or i==0 and m>1:
            #print "Max weight guess for %s :%s"%(name,results[i])
            page = wikipedia.page(results[i])
            if row['City'] in page.summary.lower():
                return page


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
        total=len(rows)
        print("Adding wikipedia data, this may take time")
        for progress,row in enumerate(rows):
            page = self.getPage(row)
            if page:
                pg+=1
                images = filter(lambda x: not x.endswith('svg'),page.images)
                row['Details'] +=(unicode(page.title)+'\n'+unicode(page.summary)+'\n'+unicode(page.content)).replace(',','#')
                row['Images URL']+=','.join(images)
            
##            sys.stdout.flush()
##            sys.stdout.write("\r%d%%"%int((float(progress)/total)*100))
            
                
        print("Pages found on wikipedis : %d/%d"%(pg,len(rows)))
            
