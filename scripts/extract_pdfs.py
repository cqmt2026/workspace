# -*- coding: utf-8 -*-
"""Extract text from all PDFs in 合同纠纷 folder"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pdfplumber

folder = r'C:\Users\Administrator\Desktop\合同纠纷'
files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
print(f"Found {len(files)} PDF files\n")

for fname in sorted(files):
    fpath = os.path.join(folder, fname)
    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print(f"{'='*60}")
    try:
        with pdfplumber.open(fpath) as pdf:
            text = ''
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + '\n'
            print(text[:3000] if len(text) > 3000 else text)
            if len(text) > 3000:
                print(f"\n... [truncated, total {len(text)} chars]")
    except Exception as e:
        print(f"Error: {e}")
