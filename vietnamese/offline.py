import sys, os, platform, re, subprocess
from anki.utils import findTag, stripHTML
from anki.hooks import addHook

try:
    from vietnamese.pystardict import Dictionary
except ImportError, e:
    if __name__ == '__main__':
        print Exception('No pystardict in PYTHONPATH. Try --local parameter.')
        exit(1)
    else:
        raise e

#hvField = "Sino-Vietnamese"
vField = "Vietnamese"
jField = "Japanese"
eField = "English"
svField  = "Sino-Vietnamese"

modelTag = "JpEnVi"
onlineTag = "JpEnVi_online"
offlineTag = "JpEnVi_offline"
#vField = "Viet"

dicts_dir = os.path.join(os.path.dirname(__file__), "dic")
dict_hanviet = Dictionary(os.path.join(dicts_dir, 'stardict-han_viet-2.4.2','hanviet'))
dict_nhatanh = Dictionary(os.path.join(dicts_dir, 'stardict-jmdict-ja-en-2.4.2','jmdict-ja-en'))
dict_nhatviet = Dictionary(os.path.join(dicts_dir, 'ovdp-japanese-vietnamese','star_nhatviet'))
dict_nhatanh_alt = Dictionary(os.path.join(dicts_dir, 'stardict-kanjidic2-2.4.2','kanjidic2'))

def cleanup_definition(definition):
  output = u''
  for line in definition.split('\n'):
    if not line.strip():
      continue
    else:
      output += '<br>%s' % line
  return output

def onFocusLost(fact, field):
    if not field.value:
        return
    
    if field.name != jField:
        #print "name <> Japanese"
        return
    
    if not findTag(modelTag, fact.model.tags):
        #print "no JpEnVi"
        return

    if not findTag(offlineTag, fact.model.tags):
        #print "no JpEnVi"
        return
    try:
        if fact[eField] or fact[svField] or fact[vField] :
            return
    except:
        return
    origText = re.sub("\[sound:.+?\]", "", field.value)
    o= origText.encode("utf-8")
    try:
        tmp = dict_hanviet[o]
        tmp = tmp.replace('\n', '<br>')
        fact[svField]=u'<b>%s</b>' % unicode(tmp, "utf-8")
    except:
        fact[svField]=u'. . . . .'

    try:
        tmp = dict_nhatanh[o]
        tmp = tmp.replace('\n', '<br>')
        fact[eField]=u'<b>%s</b>' % unicode(tmp, "utf-8")
    except:
        try:
            tmp = dict_nhatanh_alt[o]
            tmp = tmp.replace('\n', '<br>')
            fact[eField]=u'<b>%s</b>' % unicode(tmp, "utf-8")
        except:
            fact[eField]=u'. . . . .'

    try:
        tmp = dict_nhatviet[o]
        tmp = tmp.replace('\n', '<br>')
        fact[vField]=u'<b>%s</b>' % unicode(tmp, "utf-8")
    except:
        fact[vField]=u'. . . . .'
    
addHook('fact.focusLost', onFocusLost)
