from __future__ import division
import re
import itertools
import math
import string

punctuation_regex = re.compile('[%s]' % re.escape(string.punctuation))

markup_regex = re.compile(r".*sub.*sub|.*sup.*sup")

tiny_stopword_list = ["and", "or", "an", "a", "as", "at", "of", "to", "on", "for", "be", "from", "in", "by", "with", "the", "not", "but"]

def tokenize(list_of_titles):
    l = " ".join(list_of_titles)
    #remove punctuation
    l = punctuation_regex.sub('', l)
     #lowercase everything
    l = l.lower()
     #split on whitespace
    l = l.split()
    #get rid of stopwords, make sure its at least 2 letters
    return [w for w in l if w not in tiny_stopword_list and len(w) > 1 and not markup_regex.search(w) ]


def make_idf_dict(big_list):
    num_docs = len(big_list)
    idf_dict = {}
    for word in set(itertools.chain.from_iterable(big_list)):
        num_docs_appears = len([l for l in big_list if word in l])
        idf_dict[word] = math.log(num_docs/num_docs_appears)
    return idf_dict

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_tf_idf_vals(title_dict):
    return_dict = {}
    word_dict = {tup[0] : tokenize(tup[1]) for tup in title_dict.items()}
    idf_dict = make_idf_dict(word_dict.values())
    for group in word_dict:
        #calculate word histogram
        freq_dict = {}
        for w in word_dict[group]:
            freq_dict[w] = freq_dict.get(w, 0) + 1

        #get rid of numbers
        for f in freq_dict:
            if is_number(f):
                freq_dict[f] = 0
        #now, a hacky way to avoid showing similar words without going to the trouble of stemming
        for f in freq_dict:
            for f2 in freq_dict:
                if f != f2 and f in f2[:len(f)] and len(f) > 3 :
                    freq_dict[f] =  freq_dict[f] + freq_dict[f2]
                    freq_dict[f2] = 0
        final_dict = {}
        for f in freq_dict:
            final_dict[f.encode("utf-8")] = freq_dict[f] * idf_dict[f]
        return_dict[group] = final_dict
    return return_dict



