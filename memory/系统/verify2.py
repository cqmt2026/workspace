# -*- coding: utf-8 -*-
import re

def count_hanzi(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def check_chap(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'^#.*$', '', content, count=1, flags=re.M)
    content = re.sub(r'\*\*【本章完】\*\*', '', content)
    content = re.sub(r'他硬刚了.*', '', content)

    hanzi = count_hanzi(content)
    
    paras = [p.strip() for p in content.split('\n') if p.strip() and len(p.strip()) > 20]
    uniq = set(paras)
    dups = len(paras) - len(uniq)
    
    kw_list = ['逆袭', '打脸', '硬刚', '震惊', '翻盘', '碾压', '暴涨', '爆发']
    found = []
    for kw in kw_list:
        cnt = content.count(kw)
        if cnt > 0:
            found.append('%s(%d)' % (kw, cnt))
    
    return hanzi, dups, found

c9 = r'C:\Users\Administrator\.openclaw\workspace\workspace-novel\项目三：都市重生\L3-正文\第九章_出货.md'
h9, d9, kw9 = check_chap(c9)
print('Ch9: hanzi=%d dups=%d kws=%s' % (h9, d9, kw9))

c10 = r'C:\Users\Administrator\.openclaw\workspace\workspace-novel\项目三：都市重生\L3-正文\第十章_暗流.md'
h10, d10, kw10 = check_chap(c10)
print('Ch10: hanzi=%d dups=%d kws=%s' % (h10, d10, kw10))
