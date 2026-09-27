# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import pdfplumber

folder = r'C:\Users\Administrator\Desktop\合同纠纷'
out = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\物业费纠纷_提取文本.txt'
os.makedirs(os.path.dirname(out), exist_ok=True)

all_text = []
for fname in sorted(os.listdir(folder)):
    if not fname.endswith('.pdf'):
        continue
    fpath = os.path.join(folder, fname)
    all_text.append('=' * 80)
    all_text.append('FILE: ' + fname)
    all_text.append('=' * 80)
    try:
        with pdfplumber.open(fpath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    all_text.append(t)
    except Exception as e:
        all_text.append('Error: ' + str(e))

with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(all_text))
total = sum(len(t) for t in all_text)
print('Saved to', out, ', total chars:', total)
