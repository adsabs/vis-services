from __future__ import division
#using the snowball stemming algorithm, aka Porter2
from stemming.porter2 import stem
import json
import re


all = ['generate_wordcloud']


# sometimes you find words like "star - boundaries" in the text
# this removes those spaces so they can be recognized as a dashed word
collapse_regex = re.compile(r'\s*-\s*')
# these characters indicate word boundaries
split_regex = re.compile(r'[\s.();~:]+')


def list_to_dict(l):
    """
    takes awkward list of list data structure returned in solr json and dictifies it
    """
    d={}
    for index, item in enumerate(l[::2]):
        key=item
        value=l[index*2+1]
        if isinstance(value, list) and value!=[]:
            d[key]=list_to_dict(value)
        else:
            d.setdefault(key, []).append(value)
    return d


def add_punc_and_remove_redundancies(info_dict, text_list):
    '''
    takes care of the dashed word problem -- removes concatenated dashed words
    and reduces the count of tokens that were created from the dashed word
    '''

    punc_list = ["-", "/"]
    for p in punc_list:
        word_collection = []
        for t in text_list:
            if p in t and t[len(t)-1]!= p and t[0] != p:
                word_collection.append(t)

        for word in word_collection:
            tokens = word.split(p)
            full = ("").join(tokens)
            for w in info_dict:
                # replacing concatenated words in tfidf info with dashed word
                if w == full:
                    temp = info_dict[w]
                    info_dict[word] = temp
                    del info_dict[w]
                    continue
                # if word matches token instead, reduce its count
                for t in tokens:
                    if w == t:
                        info_dict[w]["tf"][0] -=1
    return info_dict


def cleanse_dict(token_freq_dict):
    '''
    a final function to get rid of anything we know we don't want
    in the json we're returning to the user
    '''

    # getting rid of super obvious url fragments in acronym and words
    for t in token_freq_dict.keys():
        lower_t = t.lower()
        if "www" in lower_t or "http" in lower_t:
            del token_freq_dict[t]
        # getting rid of anything that occurs only once
        elif token_freq_dict[t]["idf"] == 1.0:
            del token_freq_dict[t]
        # getting rid of any artifacts that have freq of 0
        elif token_freq_dict[t]["total_occurrences"] < 1:
            del token_freq_dict[t]

    return token_freq_dict


def build_dict(tf_idf_info, text_info):
    '''
    this function is responsible for taking the tfidf info, and the texts of the title
    and abstract that were returned by the solr query, and returning two dictionaries:
    a dictionary for all acronyms, and a dictionary for all other tokens
    '''

    token_freq_dict = {}
    acr_freq_dict= {}

    #iterating through individual records
    for i, _id in enumerate(tf_idf_info):
        all_data = tf_idf_info[_id]
        abstract_info = all_data.get("abstract", {})
        title_info = all_data.get("title", {})

        #text data template
        text_data = { "id": "", "title" : [""], "abstract" : ""}

        #now, update template with the actual data from solr
        text_data.update([t for t in text_info if t["id"] == _id][0])

        abstract_text = text_data["abstract"].lower()
        abstract_text = collapse_regex.sub("-", abstract_text)
        abstract_text = split_regex.split(abstract_text)

        title_text = text_data["title"][0].lower()
        title_text = collapse_regex.sub("-", title_text)
        title_text = split_regex.split(title_text)

        abstract_info = add_punc_and_remove_redundancies(abstract_info, abstract_text)
        title_info = add_punc_and_remove_redundancies(title_info, title_text)

        abstract_info.update(title_info)
        d = abstract_info

        # create the dictionaries by iterating through tokens
        for token in d:
        #ignore parts of dashed words which have already been cleaned up
        #by add_punc_and_remove_redundancies
            if d[token]["tf"][0] <= 0:
                continue
            if "syn::" in token:
                continue
            if "acr::" in token:
                acr = token[5:].upper()

                #note for later investigation: why are in some cases the same acronyms returning different idf values?

                #if the key doesn't exist, add it
                if acr not in acr_freq_dict:
                    acr_freq_dict[acr]={'total_occurrences':0, "record_count" : [], "idf" : [] }

                #add info about total occurrences, record count, and idf
                acr_freq_dict[acr]['total_occurrences']+=d[token]['tf'][0]
                acr_freq_dict[acr]["record_count"].append(_id)

                idf = d[token]['tf-idf'][0]/d[token]['tf'][0]
                acr_freq_dict[acr]['idf'].append(idf)

            # ADD WORDS longer than 2 letters
            elif len("".join([t for t in token if t.isalpha()])) > 2:
                key = stem("".join([t for t in token if t.isalpha()]))

                #add stemmed token to dictionary if the key isn't there already
                if key not in token_freq_dict:
                    token_freq_dict[key] = {"tokens" : {}, "idf" : [], "record_count" : []}

                #this records how many individual records a word appears in
                token_freq_dict[key]["record_count"].append(_id)

                #add the total tf to the specific token
                token_freq_dict[key]["tokens"][token] = token_freq_dict[key]["tokens"].get(token, 0) + d[token]['tf'][0]

                #add idf so we can take the average later
                idf = d[token]['tf-idf'][0]/d[token]['tf'][0]

                token_freq_dict[key]["idf"].append(idf)

    return token_freq_dict, acr_freq_dict



def combine_and_process_dicts(token_freq_dict, acr_freq_dict, num_records=1, min_occurrences_word=0, min_percent_word=0):
    '''
    keeping only stuff in token_freq_dict that appears > MIN_PERCENT_WORD and > MIN_occurrenceS
    creating a new dict with the most common incarnation of the token, and the total # of times
    related stemmed words appeared
    '''
    temp_dict = {}
    for t in token_freq_dict:
        most_common_t_list = sorted(token_freq_dict[t]["tokens"].items(), key=lambda x:x[1], reverse=True)
        most_common_t_list = [x for x in most_common_t_list if x[1]==most_common_t_list[0][1]]
        for c in most_common_t_list:
            # if there's a hyphenated version, we choose that
            if '-' in c[0]:
                most_common_t = c[0]
                break
        # otherwise, whatever's shortest
        else:
            most_common_t = sorted(most_common_t_list, key=lambda x:len(x[0]))[0][0]


        #how many records did this token appear in?
        record_count = len(set(token_freq_dict[t]["record_count"]))

        #in total, how often did this token appear?
        total_occurrences =  sum(token_freq_dict[t]["tokens"].values())

        #if it's negative or 0 (because it was a duplicate of an acronym), just continue
        if total_occurrences < 1:
            continue

        if record_count/num_records * 100 >= min_percent_word and total_occurrences >= min_occurrences_word:
            #find the average of all idf values
            idf = sum(token_freq_dict[t]["idf"])/len(token_freq_dict[t]["idf"])
            temp_dict[most_common_t] = {"total_occurrences": total_occurrences, "idf": idf, "record_count" : record_count}

    #storing for acr freq dict below
    old_token_freq_dict = token_freq_dict

    token_freq_dict = temp_dict

    #now also making sure acr_freq_dict only has words that appeared > MIN_PERCENT_WORD times
    temp_dict = {}

    for a in acr_freq_dict:
        record_count = len(set(acr_freq_dict[a]["record_count"]))
        total_occurrences = acr_freq_dict[a]['total_occurrences']

        #need to find a better solution
        # #keep from duplicating lower case and acronyms -- this is redundant because of the
        # #way the tokenizer works.
        # small_a = a.lower()
        # if small_a in token_freq_dict and total_occurrences > token_freq_dict[small_a]["total_occurrences"]:
        #   del token_freq_dict[small_a]
        # #the regular form of the word has more occurrences, so choose that instead
        # #and break out of this loop
        # elif small_a in token_freq_dict:
        #     continue

        if record_count/num_records * 100 >= min_percent_word and total_occurrences >= min_occurrences_word:
            idf = sum(acr_freq_dict[a]["idf"])/len(acr_freq_dict[a]["idf"])
            temp_dict[a]={"total_occurrences" : total_occurrences, "idf": idf, "record_count": record_count}

    acr_freq_dict = temp_dict

    token_freq_dict.update(acr_freq_dict)

    return token_freq_dict


def generate_wordcloud(solr_json, min_percent_word=0, min_occurrences_word=0):
    '''
    This is the main word cloud creation function.
    It takes raw solr json with tf/idf info and returns a json object that has both term
    frequency and inverse term frequency for tokens in the tf/idf info. It stems these
    tokens in order to combine their counts, choosing the most frequent word as the representative
    word
    '''
    text_info = solr_json["response"]["docs"]
    tf_idf_info = list_to_dict(solr_json['termVectors'][2:])
    num_records = len(solr_json["response"]["docs"])

    token_freq_dict, acr_freq_dict = build_dict(tf_idf_info, text_info)

    token_freq_dict = combine_and_process_dicts(token_freq_dict=token_freq_dict, acr_freq_dict=acr_freq_dict,
                            num_records = num_records, min_percent_word=min_percent_word,
                            min_occurrences_word=min_occurrences_word)

    token_freq_dict = cleanse_dict(token_freq_dict)

    return token_freq_dict

