def keywithmaxval(dic):
     """ a) create a list of the dict's keys and values;
         b) return the key with the max value"""
     v = list(dic.values())
     k = list(dic.keys())
     return k[v.index(max(v))]


def keywithminval(dic):
    """
    Return the key with the minimum non-zero value from dic.
    If all values are zero, return an arbitrary key (the first one).
    """
    # filter out zero values
    filtered_dic = {k: v for k, v in dic.items() if v != 0}
    if filtered_dic:
        # return the key with the minimum value among those that are nonzero
        return min(filtered_dic, key=filtered_dic.get)
    else:
        # if all values are zero, return the first key from the original dictionary
        return next(iter(dic), None)
