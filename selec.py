import json
import re
import random

file_path = 'cscl.json'
sfile_path = 'cscl_selected23.json'
save_file = []


with open(file_path, 'r') as csclfile:
    while csclfile.seekable():
        l = csclfile.readline()
        try:
            item = json.loads(str(l))
            update = item['update_date']
            if int(update.split('-')[0]) < 2023:
                continue
            save_file.append(item)
        except:
            break
        
# save_file = random.choices(save_file, k=100)
print(len(save_file))        

with open(sfile_path, 'w') as cscl_sfile:
    json.dump(save_file, cscl_sfile, sort_keys=True, indent=4)

