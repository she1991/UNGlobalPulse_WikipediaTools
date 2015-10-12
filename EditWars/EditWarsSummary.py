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
from lxml import html
from lxml import etree

#Get start date yyyymm
fromDate = None#'2010-06-01'
endDate = None#'2011-07-01'
#Wiki page
wikiPage = None#'Child_marriage'
#output file 
opFile = None#'editWar.json'
#the seed language
lang = None#'en'
#all language codes to be considered
opLang = None#'en'

def cmdArgs(argv) :
    global fromDate
    global endDate
    global lang
    global wikiPage
    global opFile
    global opLang
    #python EditWarsSummary.py --lang en --topic Child_marriage --fromdate 2010-06-01 --todate 2011-07-01 --oplang en -o wikiop.json
    try :
        opts, args = getopt.getopt(argv, 'ho:', ['help', 'oplang=', 'topic=', 'fromdate=', 'todate=', 'lang='])
    except getopt.GetoptError as err:
        print err
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('--lang'):
            lang = arg
        elif opt in ('-o'):
            opFile = arg
        elif opt in ('--oplang'):
            opLang = arg
        elif opt in ('--topic'):
            wikiPage = arg
        elif opt in ('--fromdate'):
            fromDate = arg
        elif opt in ('--todate'):
            endDate = arg
    if(fromDate != None and endDate != None and wikiPage != None and opFile != None and lang != None and opLang != None ) :
        #process
        sanitizeArguments()
    else :
        print 'Use as example.'
        print 'python EditWarsSummary.py --lang en --topic Child_marriage --fromdate 2010-06-01 --todate 2011-07-01 --oplang en -o wikiop.json'
        usage()
def usage() :
    print '-h\t\tPrint help'
    print '--help\t\tPrint help'
    print '-o\t\tOutput json file name'
    print '--lang\t\tWiki ISO language code of the topic'
    print '--topic\t\tWiki topic page name'
    print '--fromdate\tFrom date in yyyy-mm-dd format'
    print '--todate\tTo date in yyyy-mm-dd format'
    print '--oplang\tSpecify the language code for which the edit summary will be evaluated'
        
def sanitizeArguments() :
    global fromDate
    global endDate
    global lang
    global wikiPage
    global opFile
    global opLang
    #python EditWarsSummary.py -topic Child_marriage -fromdate 2010-06-01 -todate 2015-07-01 -oplan en -o wikiop.json
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
    #opLang must be 2 characters
    if(len(opLang) != 2):
        print '[Error] oplang code is incorrect'
        sys.exit(2)
    startScraping()

def startScraping() :
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
    #master list of all data this script gathers
    dataJson = []
    #check if opLang = lang
    if(opLang == lang) :
        editMatrix = getEditAuthorMatrix(lang, site, wikiPage)
        dataJson.append(editMatrix)
    else :
        #Go through langlinks to locate page with oplang
        gotLangFlag = False
        for ll in langLinks :
            print(ll.site.language())
            if(ll.site.language() == opLang) :
                editMatrix = getEditAuthorMatrix(ll.site.language(), ll.site, ll.title)
                dataJson.append(editMatrix)
                gotLangFlag = True
        if( not(gotLangFlag) ):
            print('A page does not exist for the given language')
    f = open(opFile,'w')
    f.write(json.dumps(dataJson, indent=4))
    f.close()

def getEditAuthorMatrix(langCode, langSite, langTitle) :
    #holds all one to one diff of consecutive edits
    revisionCache = []
    #holds all user names for revisions, a list that may even contain dupes
    revUsers = []
    page = pywikibot.Page(langSite, langTitle)
    langSite.loadrevisions(page, endtime=fromDate.isoformat(), starttime=endDate.isoformat())
    pageRevisionsList = list(page._revisions[rev] for rev in
                            sorted(page._revisions, reverse=False))
    for revision in pageRevisionsList :
        lastRevision = None
        diff = ''
        delStrength = 0
        insStrength = 0
        if(len(revisionCache) > 0):
            lastRevision = revisionCache[len(revisionCache) - 1]
            #take both revision and lastRevision and get their diff
            #print str(lastRevision['revid']) + 'versus ' + str(revision.revid)
            diff = langSite.compare(lastRevision['revid'], revision.revid)     
            #calculate addition and deletion strengths
            delStrength = getDelStrength(diff)
            insStrength = getInsStrength(diff)
        revisionCacheItem = {'timestamp':str(revision.timestamp),'revid':revision.revid, 'isbot':langSite.isBot(revision.user), 'diff':diff, 'user':revision.user, 'delStrength':delStrength, 'insStrength':insStrength}
        revUsers.append(revision.user)
        revisionCache.append(revisionCacheItem)
    #Analyse the revision cache to build the square matrix
    #get unique list of users
    uniqueRevUsers = set(revUsers)
    uniqueRevUsers = list(uniqueRevUsers)
    #make the x*x matrix
    outputMatrix = [[0 for x in range(len(uniqueRevUsers))] for x in range(len(uniqueRevUsers))]
    #Go over revision cache
    for revIndex in range (0, len(revisionCache)-1) :
        authInd = uniqueRevUsers.index((revisionCache[revIndex])['user'])
        #Add strength scores to matrix
        #find out rev author's index in uniqueRevUsers and add ins strength at that symetric location
        outputMatrix[authInd][authInd] = (revisionCache[revIndex])['insStrength']
        #print authInd
        #if this is not the first revision diffs
        if(revIndex > 0) :
            prevAuthInd = uniqueRevUsers.index((revisionCache[revIndex-1])['user'])
            #print prevAuthInd
            outputMatrix[authInd][prevAuthInd] = (revisionCache[revIndex])['delStrength']
    return ({'userArr': uniqueRevUsers, 'editMatrix': outputMatrix})
    
def getDelStrength(diff) :
    #gets the deletion strength of the revision, AKA how much of content has this revision deleted from the last one?
    delStrength = 0
    if(type(diff) is unicode and len(diff)>0) :
        diffParser = etree.HTMLParser(encoding='UTF-8')
        diffHtmlTree = etree.HTML(diff, parser=diffParser)
        dels = diffHtmlTree.xpath('//del/text()')
        delStrength = delStrength + len(dels)
    return delStrength
def getInsStrength(diff) :
    #gets the insertion strength of the revision AKA how much content has this revision inserted.
    insStrength = 0
    if(type(diff) is unicode and len(diff)>0) :
        diffParser = etree.HTMLParser(encoding='UTF-8')
        diffHtmlTree = etree.HTML(diff, parser=diffParser)
        ins = diffHtmlTree.xpath('//ins/text()')
        insStrength = insStrength + len(ins)
    return insStrength

    
def main():
    cmdArgs(sys.argv[1:])

if __name__ == "__main__": main()