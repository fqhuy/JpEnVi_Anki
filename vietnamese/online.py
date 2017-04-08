#!/usr/bin/python
#-*- coding: utf-8 -*-
# CONFIGURATION
# You can tweak the following parameters to better suit your deck/environment

# In my experience you want this to be at least 3 as some words bring up multiple
# matches, so 1 for initial list and 2 for up to 2 definitions. If latency is not
# an issue you can leave it at 6 which will dig deeper for words whose definition
# don't show up in the first results page, otherwise tune it down to 3
NUMBER_OF_FETCHES = 6

QUESTION_FIELD = 'Expression'

ANSWER_FIELD = 'Meaning'

# This will save the answers you fetch in the ANSWER_FIELD if it's empty
# Set to False to fetch each time
STORE_ANSWERS = True

# END CONFIGURATION



"""A parser for SGML, using the derived class as a static DTD."""

# XXX This only supports those SGML features used by HTML.

# XXX There should be a way to distinguish between PCDATA (parsed
# character data -- the normal case), RCDATA (replaceable character
# data -- only char and entity references and end tags are special)
# and CDATA (character data -- only end tags are special).  RCDATA is
# not supported at all.


from warnings import warnpy3k
warnpy3k("the sgmllib module has been removed in Python 3.0",
         stacklevel=2)
del warnpy3k

import markupbase
import re

# Regular expressions used for parsing

interesting = re.compile('[&<]')
incomplete = re.compile('&([a-zA-Z][a-zA-Z0-9]*|#[0-9]*)?|'
                        '<([a-zA-Z][^<>]*|'
                        '/([a-zA-Z][^<>]*)?|'
                        '![^<>]*)?')

entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile('&#([0-9]+)[^0-9]')

starttagopen = re.compile('<[>a-zA-Z]')
shorttagopen = re.compile('<[a-zA-Z][-.a-zA-Z0-9]*/')
shorttag = re.compile('<([a-zA-Z][-.a-zA-Z0-9]*)/([^/]*)/')
piclose = re.compile('>')
endbracket = re.compile('[<>]')
tagfind = re.compile('[a-zA-Z][-_.a-zA-Z0-9]*')
attrfind = re.compile(
                      r'\s*([a-zA-Z_][-:.a-zA-Z_0-9]*)(\s*=\s*'
                      r'(\'[^\']*\'|"[^"]*"|[][\-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~\'"@]*))?')


class SGMLParseError(RuntimeError):
    """Exception raised for all parse errors."""
    pass


# SGML parser base class -- find tags and call handler functions.
# Usage: p = SGMLParser(); p.feed(data); ...; p.close().
# The dtd is defined by deriving a class which defines methods
# with special names to handle tags: start_foo and end_foo to handle
# <foo> and </foo>, respectively, or do_foo to handle <foo> by itself.
# (Tags are converted to lower case for this purpose.)  The data
# between tags is passed to the parser by calling self.handle_data()
# with some data as argument (the data may be split up in arbitrary
# chunks).  Entity references are passed by calling
# self.handle_entityref() with the entity reference as argument.

class SGMLParser(markupbase.ParserBase):
    # Definition of entities -- derived classes may override
    entity_or_charref = re.compile('&(?:'
      '([a-zA-Z][-.a-zA-Z0-9]*)|#([0-9]+)'
      ')(;?)')

    def __init__(self, verbose=0):
        """Initialize and reset this instance."""
        self.verbose = verbose
        self.reset()

    def reset(self):
        """Reset this instance. Loses all unprocessed data."""
        self.__starttag_text = None
        self.rawdata = ''
        self.stack = []
        self.lasttag = '???'
        self.nomoretags = 0
        self.literal = 0
        markupbase.ParserBase.reset(self)

    def setnomoretags(self):
        """Enter literal mode (CDATA) till EOF.

        Intended for derived classes only.
        """
        self.nomoretags = self.literal = 1

    def setliteral(self, *args):
        """Enter literal mode (CDATA).

        Intended for derived classes only.
        """
        self.literal = 1

    def feed(self, data):
        """Feed some data to the parser.

        Call this as often as you want, with as little or as much text
        as you want (may include '\n').  (This just saves the text,
        all the processing is done by goahead().)
        """

        self.rawdata = self.rawdata + data
        self.goahead(0)

    def close(self):
        """Handle the remaining data."""
        self.goahead(1)

    def error(self, message):
        raise SGMLParseError(message)

    # Internal -- handle data as far as reasonable.  May leave state
    # and data to be processed by a subsequent call.  If 'end' is
    # true, force handling all data as if followed by EOF marker.
    def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.nomoretags:
                self.handle_data(rawdata[i:n])
                i = n
                break
            match = interesting.search(rawdata, i)
            if match: j = match.start()
            else: j = n
            if i < j:
                self.handle_data(rawdata[i:j])
            i = j
            if i == n: break
            if rawdata[i] == '<':
                if starttagopen.match(rawdata, i):
                    if self.literal:
                        self.handle_data(rawdata[i])
                        i = i+1
                        continue
                    k = self.parse_starttag(i)
                    if k < 0: break
                    i = k
                    continue
                if rawdata.startswith("</", i):
                    k = self.parse_endtag(i)
                    if k < 0: break
                    i = k
                    self.literal = 0
                    continue
                if self.literal:
                    if n > (i + 1):
                        self.handle_data("<")
                        i = i+1
                    else:
                        # incomplete
                        break
                    continue
                if rawdata.startswith("<!--", i):
                        # Strictly speaking, a comment is --.*--
                        # within a declaration tag <!...>.
                        # This should be removed,
                        # and comments handled only in parse_declaration.
                    k = self.parse_comment(i)
                    if k < 0: break
                    i = k
                    continue
                if rawdata.startswith("<?", i):
                    k = self.parse_pi(i)
                    if k < 0: break
                    i = i+k
                    continue
                if rawdata.startswith("<!", i):
                    # This is some sort of declaration; in "HTML as
                    # deployed," this should only be the document type
                    # declaration ("<!DOCTYPE html...>").
                    k = self.parse_declaration(i)
                    if k < 0: break
                    i = k
                    continue
            elif rawdata[i] == '&':
                if self.literal:
                    self.handle_data(rawdata[i])
                    i = i+1
                    continue
                match = charref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_charref(name)
                    i = match.end(0)
                    if rawdata[i-1] != ';': i = i-1
                    continue
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    i = match.end(0)
                    if rawdata[i-1] != ';': i = i-1
                    continue
            else:
                self.error('neither < nor & ??')
            # We get here only if incomplete matches but
            # nothing else
            match = incomplete.match(rawdata, i)
            if not match:
                self.handle_data(rawdata[i])
                i = i+1
                continue
            j = match.end(0)
            if j == n:
                break # Really incomplete
            self.handle_data(rawdata[i:j])
            i = j
        # end while
        if end and i < n:
            self.handle_data(rawdata[i:n])
            i = n
        self.rawdata = rawdata[i:]
        # XXX if end: check for empty stack

    # Extensions for the DOCTYPE scanner:
    _decl_otherchars = '='

    # Internal -- parse processing instr, return length or -1 if not terminated
    def parse_pi(self, i):
        rawdata = self.rawdata
        if rawdata[i:i+2] != '<?':
            self.error('unexpected call to parse_pi()')
        match = piclose.search(rawdata, i+2)
        if not match:
            return -1
        j = match.start(0)
        self.handle_pi(rawdata[i+2: j])
        j = match.end(0)
        return j-i

    def get_starttag_text(self):
        return self.__starttag_text

    # Internal -- handle starttag, return length or -1 if not terminated
    def parse_starttag(self, i):
        self.__starttag_text = None
        start_pos = i
        rawdata = self.rawdata
        if shorttagopen.match(rawdata, i):
            # SGML shorthand: <tag/data/ == <tag>data</tag>
            # XXX Can data contain &... (entity or char refs)?
            # XXX Can data contain < or > (tag characters)?
            # XXX Can there be whitespace before the first /?
            match = shorttag.match(rawdata, i)
            if not match:
                return -1
            tag, data = match.group(1, 2)
            self.__starttag_text = '<%s/' % tag
            tag = tag.lower()
            k = match.end(0)
            self.finish_shorttag(tag, data)
            self.__starttag_text = rawdata[start_pos:match.end(1) + 1]
            return k
        # XXX The following should skip matching quotes (' or ")
        # As a shortcut way to exit, this isn't so bad, but shouldn't
        # be used to locate the actual end of the start tag since the
        # < or > characters may be embedded in an attribute value.
        match = endbracket.search(rawdata, i+1)
        if not match:
            return -1
        j = match.start(0)
        # Now parse the data between i+1 and j into a tag and attrs
        attrs = []
        if rawdata[i:i+2] == '<>':
            # SGML shorthand: <> == <last open tag seen>
            k = j
            tag = self.lasttag
        else:
            match = tagfind.match(rawdata, i+1)
            if not match:
                self.error('unexpected call to parse_starttag')
            k = match.end(0)
            tag = rawdata[i+1:k].lower()
            self.lasttag = tag
        while k < j:
            match = attrfind.match(rawdata, k)
            if not match: break
            attrname, rest, attrvalue = match.group(1, 2, 3)
            if not rest:
                attrvalue = attrname
            else:
                if (attrvalue[:1] == "'" == attrvalue[-1:] or
                    attrvalue[:1] == '"' == attrvalue[-1:]):
                    # strip quotes
                    attrvalue = attrvalue[1:-1]
                attrvalue = self.entity_or_charref.sub(
                    self._convert_ref, attrvalue)
            attrs.append((attrname.lower(), attrvalue))
            k = match.end(0)
        if rawdata[j] == '>':
            j = j+1
        self.__starttag_text = rawdata[start_pos:j]
        self.finish_starttag(tag, attrs)
        return j

    # Internal -- convert entity or character reference
    def _convert_ref(self, match):
        if match.group(2):
            return self.convert_charref(match.group(2)) or \
                '&#%s%s' % match.groups()[1:]
        elif match.group(3):
            return self.convert_entityref(match.group(1)) or \
                '&%s;' % match.group(1)
        else:
            return '&%s' % match.group(1)

    # Internal -- parse endtag
    def parse_endtag(self, i):
        rawdata = self.rawdata
        match = endbracket.search(rawdata, i+1)
        if not match:
            return -1
        j = match.start(0)
        tag = rawdata[i+2:j].strip().lower()
        if rawdata[j] == '>':
            j = j+1
        self.finish_endtag(tag)
        return j

    # Internal -- finish parsing of <tag/data/ (same as <tag>data</tag>)
    def finish_shorttag(self, tag, data):
        self.finish_starttag(tag, [])
        self.handle_data(data)
        self.finish_endtag(tag)

    # Internal -- finish processing of start tag
    # Return -1 for unknown tag, 0 for open-only tag, 1 for balanced tag
    def finish_starttag(self, tag, attrs):
        try:
            method = getattr(self, 'start_' + tag)
        except AttributeError:
            try:
                method = getattr(self, 'do_' + tag)
            except AttributeError:
                self.unknown_starttag(tag, attrs)
                return -1
            else:
                self.handle_starttag(tag, method, attrs)
                return 0
        else:
            self.stack.append(tag)
            self.handle_starttag(tag, method, attrs)
            return 1

    # Internal -- finish processing of end tag
    def finish_endtag(self, tag):
        if not tag:
            found = len(self.stack) - 1
            if found < 0:
                self.unknown_endtag(tag)
                return
        else:
            if tag not in self.stack:
                try:
                    method = getattr(self, 'end_' + tag)
                except AttributeError:
                    self.unknown_endtag(tag)
                else:
                    self.report_unbalanced(tag)
                return
            found = len(self.stack)
            for i in range(found):
                if self.stack[i] == tag: found = i
        while len(self.stack) > found:
            tag = self.stack[-1]
            try:
                method = getattr(self, 'end_' + tag)
            except AttributeError:
                method = None
            if method:
                self.handle_endtag(tag, method)
            else:
                self.unknown_endtag(tag)
            del self.stack[-1]

    # Overridable -- handle start tag
    def handle_starttag(self, tag, method, attrs):
        method(attrs)

    # Overridable -- handle end tag
    def handle_endtag(self, tag, method):
        method()

    # Example -- report an unbalanced </...> tag.
    def report_unbalanced(self, tag):
        if self.verbose:
            print '*** Unbalanced </' + tag + '>'
            print '*** Stack:', self.stack

    def convert_charref(self, name):
        """Convert character reference, may be overridden."""
        try:
            n = int(name)
        except ValueError:
            return
        if not 0 <= n <= 127:
            return
        return self.convert_codepoint(n)

    def convert_codepoint(self, codepoint):
        return chr(codepoint)

    def handle_charref(self, name):
        """Handle character reference, no need to override."""
        replacement = self.convert_charref(name)
        if replacement is None:
            self.unknown_charref(name)
        else:
            self.handle_data(replacement)

    # Definition of entities -- derived classes may override
    entitydefs = \
            {'lt': '<', 'gt': '>', 'amp': '&', 'quot': '"', 'apos': '\''}

    def convert_entityref(self, name):
        """Convert entity references.

        As an alternative to overriding this method; one can tailor the
        results by setting up the self.entitydefs mapping appropriately.
        """
        table = self.entitydefs
        if name in table:
            return table[name]
        else:
            return

    def handle_entityref(self, name):
        """Handle entity references, no need to override."""
        replacement = self.convert_entityref(name)
        if replacement is None:
            self.unknown_entityref(name)
        else:
            self.handle_data(replacement)

    # Example -- handle data, should be overridden
    def handle_data(self, data):
        pass

    # Example -- handle comment, could be overridden
    def handle_comment(self, data):
        pass

    # Example -- handle declaration, could be overridden
    def handle_decl(self, decl):
        pass

    # Example -- handle processing instruction, could be overridden
    def handle_pi(self, data):
        pass

    # To be overridden -- handlers for unknown objects
    def unknown_starttag(self, tag, attrs): pass
    def unknown_endtag(self, tag): pass
    def unknown_charref(self, ref): pass
    def unknown_entityref(self, ref): pass


class TestSGMLParser(SGMLParser):

    def __init__(self, verbose=0):
        self.testdata = ""
        SGMLParser.__init__(self, verbose)

    def handle_data(self, data):
        self.testdata = self.testdata + data
        if len(repr(self.testdata)) >= 70:
            self.flush()

    def flush(self):
        data = self.testdata
        if data:
            self.testdata = ""
            print 'data:', repr(data)

    def handle_comment(self, data):
        self.flush()
        r = repr(data)
        if len(r) > 68:
            r = r[:32] + '...' + r[-32:]
        print 'comment:', r

    def unknown_starttag(self, tag, attrs):
        self.flush()
        if not attrs:
            print 'start tag: <' + tag + '>'
        else:
            print 'start tag: <' + tag,
            for name, value in attrs:
                print name + '=' + '"' + value + '"',
            print '>'

    def unknown_endtag(self, tag):
        self.flush()
        print 'end tag: </' + tag + '>'

    def unknown_entityref(self, ref):
        self.flush()
        print '*** unknown entity ref: &' + ref + ';'

    def unknown_charref(self, ref):
        self.flush()
        print '*** unknown char ref: &#' + ref + ';'

    def unknown_decl(self, data):
        self.flush()
        print '*** unknown decl: [' + data + ']'

    def close(self):
        SGMLParser.close(self)
        self.flush()


#------------------------------------------------------------------------------------------------------------------------------------------------
import sys, os, platform, re, subprocess
#from anki.utils import findTag, stripHTML
from anki.hooks import addHook

from ankiqt import mw
from ankiqt import ui
from anki.latex import renderLatex
from anki.sound import playFromText, stripSounds
from anki.models import CardModel, formatQA
from anki.utils import parseTags, findTag, stripHTML, genID, hexifyID
from anki.utils import canonifyTags

import random
#import sys
import urllib
import urllib2


vField = "Vietnamese"
jField = "Japanese"
eField = "English"
svField  = "Sino-Japanese"
exField = "Example"
modelTag = "JpEnVi"
onlineTag = "JpEnVi_online"
offlineTag = "JpEnVi_offline"
brs_o = ['<br />[<br />','<br>[<br>','<br/>[<br/>']
brs_c = ['<br />]<br />','<br>]<br>','<br/>]<br/>','<br>] <br>']
#vField = "Viet"
class Definition:
    def __init__(self):
        self.name = u''
        self.examples = []

class DefinitionParser(SGMLParser):
    def __init__(self, search_term, verbose=0):
        SGMLParser.__init__(self, verbose)
        self.search_term = search_term
        self.parse_definition = False

        self.parse_content = False
        self.definitions = []
        self.content = u''

    def start_div(self, attrs):
        for k,v in attrs:
            if k=='id' and v=='content-3':
                self.parse_content = True
                self.content = u''

    def end_div(self):
        self.parse_content = False

    def handle_data(self, data):
        if self.parse_content:
            self.definitions.append(data)

def get_output(parser):
  output = u''
  for definition in parser.definitions:
      output = u'%s<div align=left>%s</div>' % (output, definition)#cleanup_definition(definition.name))
  return output

def get_random_user_agent():
  user_agents = [
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727)'
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9b5) Gecko/2008032619 Firefox/3.0b5',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)'
  ]
  return random.choice(user_agents)

def online_search(term, dictionary):
    output = u''
    #done_searching = False
    search_urls = []
    headers = {'User-Agent': get_random_user_agent()}
    base_url = 'http://tratu.vn'
    my_term = urllib.quote(term.encode('utf-8'))
  
    if dictionary == 'jp_vn':
        search_urls.append(u'/dict/jp_vn/%s' % my_term)
    if dictionary == 'vn_jp':
        search_urls.append(u'/dict/vn_jp/%s' % my_term)
    num_requests = 0
    while search_urls:
        num_requests += 1
        if num_requests > NUMBER_OF_FETCHES:
            break
        try:
            search_url = search_urls.pop(0)

            # check the cache first

            parser = DefinitionParser(term)
            request = urllib2.Request(u'%s%s' % (base_url, search_url), headers=headers)
            url = urllib2.urlopen(request)
            page = unicode(url.read(), 'utf-8', errors='ignore')

            parser.feed(page)
            url.close()
            parser.close()
        
      
            output += get_output(parser)

        except Exception, e:
            output+= '. . . . .'
            #output += '<div align=left>ERROR: %s: %s%s</div>' % (e, base_url, search_url)
    return output

def onFocusLost_online(fact, field):
    if not field.value:
        return
    if field.name != jField:
        #print "name <> Japanese"
        return

    if not findTag(modelTag, fact.model.tags):
        #print "no JpEnVi"
        return
    if not findTag(onlineTag, fact.model.tags):
        #print "no JpEnVi"
        return
    try:
        if fact[exField]:
            return
    except:
        return
    origText = re.sub("\[sound:.+?\]", "", field.value)
    tmp = u''
    tmp = online_search(origText,'jp_vn')


    fact[exField] = tmp #unicode(tmp, "utf-8")
    
addHook('fact.focusLost', onFocusLost_online)
