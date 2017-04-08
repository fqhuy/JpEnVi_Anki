# -*- coding: utf-8 -*-
# Copyright: Phan Quoc Huy
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

def init():
    import vietnamese.model
    import vietnamese.offline
    import vietnamese.online

from ankiqt import mw
mw.registerPlugin("JpEnVi Support", 173)

from anki.hooks import addHook
addHook('init', init)
