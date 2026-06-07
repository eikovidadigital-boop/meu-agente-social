# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
from image.story_arte import montar_story, SW, SH
from image.arte_informativo import frasco_demo

def test_story_size():
    art = montar_story(frasco_demo("120 ml"), "Rosa Mosqueta", "PELE", ["Regenera","Ilumina","Renova"])
    assert art.size == (SW, SH) == (1080, 1920)

def test_story_30ml():
    art = montar_story(frasco_demo("30 ml"), "Limão", "PELE", ["Purifica","Refresca","Tonifica"])
    assert art.size == (1080, 1920)

if __name__ == "__main__":
    test_story_size(); test_story_30ml(); print("test_story OK")
