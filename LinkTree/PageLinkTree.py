import pywikibot
import json
import requests
import time
from datetime import datetime, date
import sys
import getopt

lang = None
wikiPage = None
opFile = None
opLang = None

#Start from first page
def cmdArgs(argv) :
    global lang
    global wikiPage
    global opFile

    try :
        opts, args = getopt.getopt(argv, 'ho:', ['help', 'topic=', 'lang='])
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
        elif opt in ('--topic'):
            wikiPage = arg
    if( wikiPage != None and opFile != None and lang != None ) :
        #process
        sanitizeArguments()
    else :
        print 'Use as example.'
        print 'python PageLinkTree.py --lang en --topic Child_marriage -o wikiop.json'
        usage()
def usage() :
    print '-h\t\tPrint help'
    print '--help\t\tPrint help'
    print '-o\t\tOutput json file name'
    print '--lang\t\tWiki ISO language code'
    print '--topic\t\tWiki topic page name in language'
        
def sanitizeArguments() :
    global lang
    global wikiPage
    global opFile

    if(len(lang) != 2):
        print '[Error] language code is incorrect'
        sys.exit(2)
    startScraping()

def startScraping() :
    global wikiPage
    global lang
    global opFile 
    global langCodes
    
    site = pywikibot.Site(lang,u'wikipedia')
    page = pywikibot.Page(site, wikiPage)
    dataJson = []
    linkObj = { 'name': wikiPage,  'children': [] }
    mapLinks(linkObj, site, 3)
    dataJson.append(linkObj)
    f = open(opFile,'w')
    f.write(json.dumps(dataJson, indent=3))
    f.close()
    
    
#each link represented as {name: 'page_name_here', children : [{name: 'child's_name_here', children:[....]}]}
def mapLinks(linkObj, site, levelsDown) :
    print (linkObj)
    print (levelsDown)
    if(levelsDown <= 0) :
        return;
    #make a pywikibot page object
    page = pywikibot.Page( site, linkObj['name'] )
    #get page's links
    wikiLinks = page.linkedPages()
    #iterate these linked page links
    for wikiLink in wikiLinks :
        #Make a link JSON object
        wikiLinkObj = {'name': wikiLink.title(), 'children': []}
        #add those links to the page parameters children member
        linkObj['children'].append(wikiLinkObj)
        #call mapLinks on each of these page objects
        mapLinks(wikiLinkObj, site, (levelsDown - 1))

def main():
    cmdArgs(sys.argv[1:])

if __name__ == "__main__": main()
