# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Standard Japanese model.
#

from anki.models import Model, CardModel, FieldModel
import anki.stdmodels

def JpEnViModel():
    m = Model(_("JpEnVi"))
    # expression
    f = FieldModel(u'Japanese', True, True)
    font = u"Mincho"
    f.quizFontSize = 50
    f.quizFontFamily = font
    f.editFontFamily = font
    m.addFieldModel(f)
    # meaning
    f = FieldModel(u'English', False, False)
    font = u"Mincho"
    f.quizFontSize = 20
    f.quizFontFamily = font
    f.editFontFamily = font
    m.addFieldModel(f)
    # reading
    f = FieldModel(u'Sino-Vietnamese', False, False)#for Kanji only (?)
    font = u"Arial"
    f.quizFontSize = 20
    f.quizFontFamily = font
    f.editFontFamily = font
    m.addFieldModel(f)
    #vietnamese
    f = FieldModel(u'Vietnamese', False, False)
    font = u"Mincho"
    f.quizFontSize = 20
    f.quizFontFamily = font
    f.editFontFamily = font
    m.addFieldModel(f)

    f = FieldModel(u'Example', False, False)
    font = u"Mincho"
    f.quizFontSize = 20
    f.quizFontFamily = font
    f.editFontFamily = font	
    m.addFieldModel(f)

    m.addCardModel(CardModel(u"Recognition",
                   u"%(Japanese)s",
                   u"<div align='left'>English</div><hr> <br> %(English)s <div align='left'>Sino-Vietnamese</div><hr><br>%(Sino-Vietnamese)s <div align='left'>Vietnamese</div><hr><br>%(Vietnamese)s <div align='left'>Examples from tratu.vn</div><hr><br>%(Example)s"))
    m.addCardModel(CardModel(u"Recall",
                             u"%(Vietnamese)s",
                             u"%(Japanese)s",
                             active=False))

    m.tags = u"JpEnVi, JpEnVi_offline"
    return m

anki.stdmodels.models['JpEnVi'] = JpEnViModel
