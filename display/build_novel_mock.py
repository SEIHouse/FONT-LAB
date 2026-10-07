"""Make the NovelExpanded mock consume the same runtime shipped in the package."""
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from display.build_living_package import build, PACKAGE


def build_mock():
    """Copy the public built core and player into the website's module inventory."""
    build()
    target=ROOT/'display/novel-expanded/runtime';target.mkdir(parents=True,exist_ok=True)
    for name in ('engine.js','index.js','player.js'):
        shutil.copyfile(PACKAGE/'dist'/name,target/name)
    print('NovelExpanded mock: consumes the installable Living Titles runtime')


if __name__=='__main__':build_mock()
