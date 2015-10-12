import pywikibot
import json
import requests
import time
from datetime import datetime, date
import sys
import getopt

#Get start date yyyymm
fromDate = None
endDate = None
#Wiki page
wikiPage = None
viewStatsURL = 'http://stats.grok.se/json'
#output file 
opFile = None
#global verbose flag
globalVerbose = False
#the seed language
lang = None
#all language codes to be considered
langCodes = []

#python scrapeViewsEdits -lang en -topic Child_marriage -fromdate 2010-06-01 -todate 2015-07-01 -o wikiop.json -v --langlinks hi,ru
def cmdArgs(argv) :
    global globalVerbose
    global wikiPage
    global fromDate
    global endDate
    global lang
    global opFile
    global langCodes
    try :
        opts, args = getopt.getopt(argv, 'vho:', ['help', 'lang=', 'topic=', 'fromdate=', 'todate=', 'langlinks='])
    except getopt.GetoptError as err:
        print err
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-o'):
            opFile = arg
        elif opt in ('--v'):
            globalVerbose = True
        elif opt in ('--lang'):
            lang = arg
        elif opt in ('--topic'):
            wikiPage = arg
        elif opt in ('--fromdate'):
            fromDate = arg
        elif opt in ('--todate'):
            endDate = arg
        elif opt in ('--langlinks'):
            langCodes = arg.split(',')
            print langCodes
    if(fromDate != None and endDate != None and wikiPage != None and opFile != None and lang != None and len(langCodes) > 0) :
        #process
        sanitizeArguments()
    else :
        print 'Use as example.'
        print 'python scrapeViewsEdits --lang en --topic Child_marriage --fromdate 2010-06-01 --todate 2015-07-01 -o wikiop.json -v --langlinks hi,ru,de'
        usage()
def usage() :
    print '-h\t\tPrint help'
    print '--help\t\tPrint help'
    print '-o\t\tOutput json file name'
    print '-v\t\tVerbose'
    print '--lang\t\tWiki ISO language code'
    print '--topic\t\tWiki topic page name'
    print '--fromdate\tFrom date in yyyy-mm-dd format'
    print '--todate\tTo date in yyyy-mm-dd format'
    print '--langlinks\tSpecify the comma separated list of languages codes to consider'
def sanitizeArguments() :
    global fromDate
    global endDate
    global lang
    #Make date objects from fromDate
    fromDate = datetime.strptime(fromDate.strip(), '%Y-%m-%d')
    #Make date objects from toDate
    endDate = datetime.strptime(endDate.strip(), '%Y-%m-%d')
    #toDate>fromDate
    if(fromDate > endDate) :
        print '[Error] fromdate cannot be greater than todate'
        sys.exit(2);
    #check if the todate is not greater than today!
    if(endDate > datetime.today()) :
        print '[Error] todate cannot be greater than today'
        sys.exit(2)
    #lang must be 2 characters long
    if(len(lang) != 2):
        print '[Error] language code is incorrect'
        sys.exit(2)
    #if everything is okay, order startScraping
    startScraping()
def startScraping() :
    global globalVerbose
    global wikiPage
    global fromDate
    global endDate
    global lang
    global opFile 
    global langCodes
    #Detect all available languages for a wiki page
    #TODO: use user-config.py lang and family here
    site = pywikibot.Site(lang,u'wikipedia')
    page = pywikibot.Page(site, wikiPage)
    #get all language links for this page
    langLinks = site.pagelanglinks(page)
    #TODO: use user-config.py lang here

    #master list of all data this script gathers
    dataJson = []
    #first we gather the view and revision stats for the seed page
    seedStats = gatherStats(u'en', site, wikiPage)
    dataJson.append(seedStats)
    for ll in langLinks :
        if(langCodes.count(ll.site.language()) > 0) :
            langStats = gatherStats(ll.site.language(), ll.site, ll.title)
            dataJson.append(langStats)
    f = open(opFile,'w')
    f.write(json.dumps(dataJson, indent=4))
    f.close()  
def gatherStats(langCode, langSite, langTitle) :
    #STEP 1: Call http://stats.grok.se/ for the language and topic
    #iterate from start date
    #object made for each language will contain view stats and edit events
    langViewStats = []
    startDate = int(fromDate.strftime('%Y%m'))
    while startDate <= int(endDate.strftime('%Y%m')) :
        #Don't want to DOS the server.
        time.sleep(3)
        #append all view stats information to this object-
        request = requests.get(viewStatsURL+'/'+langCode+'/'+str(startDate)+'/'+langTitle)
        for stat in request.json()['daily_views'].items() :
            #create a json for the key value pair
            statJson = {'date':str(stat[0]), 'views':stat[1]}
            #append to list langViewStats
            langViewStats.append(statJson)
        #increment the startDate
        if(startDate % 100 == 12) :
            startDate = startDate - 11
            startDate = startDate + 100
        else :
            startDate = startDate + 1
    #STEP 2: Gather edit dates for this language wiki
    page = pywikibot.Page(langSite, langTitle)
    langSite.loadrevisions(page, endtime=fromDate.isoformat(), starttime=endDate.isoformat())
    pageRevisionsList = list(page._revisions[rev] for rev in
                            sorted(page._revisions, reverse=False))
    pageRevStats = []
    for revision in pageRevisionsList :
        revJson = {'timestamp':str(revision.timestamp),'revid':revision.revid, 'isbot':langSite.isBot(revision.user)}
        pageRevStats.append(revJson)
    
    #Add pageRevStats and langViewStats to the langDataJson which holds all stats for 
    #this particular language
    langDataJson = {'lang':langCode, 'views':langViewStats, 'revisions':pageRevStats}
    #now return this
    return langDataJson

def main():
    cmdArgs(sys.argv[1:])

if __name__ == "__main__": main()