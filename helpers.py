def keywithmaxval(dic):
     """ a) create a list of the dict's keys and values;
         b) return the key with the max value"""
     v = list(dic.values())
     k = list(dic.keys())
     return k[v.index(max(v))]


def keywithminval(dic):
    """ a) create a list of the dict's keys and values;
        b) return the key with the min value only if it's not 0"""
    # filter out zero values
    filtered_dic = {k: v for k, v in dic.items() if v != 0}
    if not filtered_dic:
        return None
    v = list(filtered_dic.values())
    k = list(filtered_dic.keys())
    return k[v.index(min(v))]
