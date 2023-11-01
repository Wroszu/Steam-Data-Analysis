import pandas as pd
from ast import literal_eval

#%%

if __name__ == '__main__':

    hhii = "[{'id': 1, 'description': 'Multi-player'}, {'id': 36, 'description': 'Online Multi-Player'}, {'id': 37, 'description': 'Local Multi-Player'}]"
    p = literal_eval(hhii)
    type(p)
    print(p)

    k = ';'.join(c['description'] for c in p)
    type(k)
    
#%%