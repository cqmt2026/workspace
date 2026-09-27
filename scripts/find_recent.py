import os, glob, datetime

all_files = []
for root, dirs, files in os.walk(r'C:\Users\Administrator\.openclaw\workspace'):
    for f in files:
        path = os.path.join(root, f)
        try:
            mtime = os.path.getmtime(path)
            all_files.append((mtime, path))
        except:
            pass

all_files.sort(key=lambda x: x[0], reverse=True)
for mtime, path in all_files[:25]:
    dt = datetime.datetime.fromtimestamp(mtime)
    rel = os.path.relpath(path, r'C:\Users\Administrator\.openclaw\workspace')
    date_str = dt.strftime('%m-%d %H:%M')
    print(f'{date_str} {rel}')
