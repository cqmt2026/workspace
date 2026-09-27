import os
for root, dirs, files in os.walk(r'C:\Users\Administrator\.agents\skills'):
    for d in dirs:
        print(os.path.join(root, d))
