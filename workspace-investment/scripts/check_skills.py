import os
for root, dirs, files in os.walk(r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills'):
    for d in dirs:
        print(os.path.join(root, d))
    break
