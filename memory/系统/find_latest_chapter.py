import os
import sys

os.chdir(r"C:\Users\Administrator\.openclaw\workspace\workspace-novel\项目一：鉴城师\L4-shared\正文")

# List all md files with their actual filenames (bytes)
files = [f for f in os.listdir('.') if f.endswith('.md')]
for f in files:
    print(repr(f))
