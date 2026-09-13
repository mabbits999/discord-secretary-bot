#!/usr/bin/env python3
"""web/hub.html（アーティファクト用の本文だけのファイル）を、
Xserver などに置ける完全なHTML（web/dist/index.html）に変換する。"""
import pathlib

here = pathlib.Path(__file__).resolve().parent
src = (here / "hub.html").read_text(encoding="utf-8")
head_end = src.index("</style>") + len("</style>")
head, body = src[:head_end], src[head_end:]

doc = (
    "<!doctype html>\n<html lang=\"ja\">\n<head>\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<meta name=\"robots\" content=\"noindex, nofollow\">\n"
    + head.strip() + "\n</head>\n<body>" + body.rstrip() + "\n</body>\n</html>\n"
)
out = here / "dist" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(doc, encoding="utf-8")
print(f"wrote {out} ({len(doc.encode('utf-8'))} bytes)")
