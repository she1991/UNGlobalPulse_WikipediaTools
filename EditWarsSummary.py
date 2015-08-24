#Cache Revisions 
#revid, user, diff content
#revision diff contents are chained diffs, meaning for revision n
#their diff content will be diff(n,n-1)

import pywikibot
import json
import requests
import time
from datetime import datetime, date
import sys
import getopt
import codecs

#Get start date yyyymm
fromDate = '2010-06-01'
endDate = '2015-07-01'
#Wiki page
wikiPage = 'Child_marriage'
#output file 
opFile = 'editWar.json'
#global verbose flag
globalVerbose = False
#the seed language
lang = 'en'
#all language codes to be considered
langCodes = ['hi']

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
    revisionCache = []
    page = pywikibot.Page(langSite, langTitle)
    langSite.loadrevisions(page, endtime=fromDate.isoformat(), starttime=endDate.isoformat())
    pageRevisionsList = list(page._revisions[rev] for rev in
                            sorted(page._revisions, reverse=False))
    file = codecs.open("lol", "a", "utf-8")
    for revision in pageRevisionsList :
        lastRevision = None
        diff = ''
        if(len(revisionCache) > 0):
            lastRevision = revisionCache[len(revisionCache) - 1]
            #take both revision and lastRevision and get their diff
            print str(lastRevision['revid']) + 'versus ' + str(revision.revid)
            diff = langSite.compare(lastRevision['revid'], revision.revid)
        file.write(diff)       
        revisionCacheItem = {'timestamp':str(revision.timestamp),'revid':revision.revid, 'isbot':langSite.isBot(revision.user), 'diff':diff}
        revisionCache.append(revisionCacheItem)
    file.close()
sanitizeArguments()
