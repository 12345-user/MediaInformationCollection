# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\Tools\creator-monitor')
from database.db import init_db, get_all_creators
init_db()
print('DB initialized OK')
creators = get_all_creators()
print(f'Creators in DB: {len(creators)}')
