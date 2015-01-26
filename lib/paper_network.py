'''
Created on Mar 4, 2014

@author: ehenneken
'''

# general module imports
import sys
import os
import time
import operator
import histeq
from numpy import mat
from numpy import zeros
from numpy import fill_diagonal
from numpy import sqrt, ones, multiply, array
import numpy

import networkx as nx
import community
import math
from networkx.readwrite import json_graph
from collections import defaultdict 

import tf_idf

__all__ = ['get_papersnetwork']

# Helper functions
def _get_reference_mapping(data):
    '''
    Construct the reference dictionary for a set of bibcodes
    '''
    refdict = {}
    for doc in data:
        if 'reference' in doc:
            refdict[doc['bibcode']] = set(doc['reference'])
    return refdict

def _get_paper_data(data):
    '''
    Extract article info from Solr data
    '''
    infodict = {}
    for doc in data:
        infodict[doc['bibcode']] = doc
    return infodict

def _sort_and_cut_results(resdict,cutoff=1500):
    '''
    Sort dictionary by its values and cut list at a prefixed value of items
    '''
    if len(resdict) <= cutoff:
        return resdict
    else:
        # first sort the dictionary
        sorted_list = sorted(resdict.iteritems(), key=operator.itemgetter(1), reverse=True)
        # then cut the list to one of length 'cutoff'
        cut_sorted_list = sorted_list[:cutoff]
        # and finally contruct the smaller results dictionary
        cutdict = {}
        for index in cut_sorted_list:
            cutdict[index[0]] = index[1]
        return cutdict

#Alex's function that takes a generated graph and gives you back a graph with groups

def augment_graph_data(data, max_groups):

  total_nodes = len(data['nodes'])   

  #lowering the necessary node count
  #since in some cases node count is greatly reduced after processing
  # first author kurtz,m goes from ~60 to 19 for instance

  if total_nodes < 15:
    
    return {"fullGraph" :data}
  
  #create the networkx graph
  G = nx.Graph()
  for i,x in enumerate(data['nodes']):
    G.add_node(i, node_name= x["node_name"], nodeWeight = x["nodeWeight"], title=x["title"], citation_count=x["citation_count"], first_author = x["first_author"], read_count = x["read_count"])

  for i,x in enumerate(data['links']):
    G.add_edge(x["source"], x["target"], weight = x["value"], overlap = list(x["overlap"]))
   
  all_nodes = G.nodes()
  
  #partition is a dictionary with group names as keys
  # and individual node indexes as values
  partition = community.best_partition(G)

  for g in G.nodes():
    G.node[g]["group"] = partition[g]

  #with new group info, create the summary group graph
  summary_graph = community.induced_graph(partition, G)

  #title container
  titles = {}

  #enhance the information that will be in the json handed off to d3
  for x in summary_graph.nodes():
    summary_graph.node[x]["total_citations"] = sum([G.node[paper].get("citation_count", 0) for paper in G.nodes() if G.node[paper]["group"] == x])
    summary_graph.node[x]["total_reads"] = sum([G.node[paper].get("read_count", 0) for paper in G.nodes() if G.node[paper]["group"] == x])
    papers = sorted([G.node[paper] for paper in G.nodes() if G.node[paper]["group"] == x], key = lambda x: x.get("nodeWeight", 0), reverse = True)
    titles[x] = [p["title"]for p in papers]
    summary_graph.node[x]["paper_count"] = len(papers)

  return titles



  #attaching title 'word clouds' to the nodes
  significant_words = tf_idf.get_tf_idf_vals(titles)
  for x in summary_graph.nodes():
    #remove the ones with only 1 paper
    if summary_graph.node[x]["paper_count"] == 1:
      summary_graph.remove_node(x)
    else:
      #otherwise, give them a title
      #how many words should we show on the group? max 6, otherwise 1 per every 2 papers
      summary_graph.node[x]["node_label"] =  dict(sorted(significant_words[x].items(), key = lambda x: x[1], reverse = True)[:6])


 #remove all but top n groups from summary graph
 #where top n is measured by total citations from a group
  top_nodes = sorted([n for n in summary_graph.nodes(data = True)], key= lambda x : x[1]["total_citations"], reverse = True )[:max_groups]
  top_nodes = [t for t in top_nodes if t >=1]
  top_node_ids = [n[0] for n in top_nodes]
  for group_id in summary_graph.nodes():
    if group_id not in top_node_ids:
      summary_graph.remove_node(group_id)

 #remove nodes from full graph that aren't in top group
 #this automatically takes care of edges, too
  for node in G.nodes(data = True):
    if node[1]["group"] not in top_node_ids:
      G.remove_node(node[0])


 #continuing to enhance the information: add to group info about the most common co-references
  for x in summary_graph.nodes():
    #make a float so division later to get a percent makes sense
    num_papers =  float(summary_graph.node[x]["paper_count"])
    references = {}
    #find all members of group x
    indexes =  [paperIndex for paperIndex in G.nodes() if G.node[paperIndex]["group"] == x]
    for edge in G.edges(data=True):
        #if it passes, it's an inter-group connection
        # [0] is source, [1] is target, [2] is data dict
        paper_one = edge[0]
        paper_two = edge[1]
        if paper_one in indexes and paper_two in indexes:
            for bib in edge[2]["overlap"]:
                if bib in references:
                    references[bib].update([paper_one, paper_two])
                else:
                    references[bib] = set([paper_one, paper_two])

    count_references = sorted(references.items(), key=lambda x:len(x[1]), reverse = True)[:5]
    top_common_references = [(tup[0], float("{0:.2f}".format(len(tup[1])/num_papers))) for tup in count_references]
    top_common_references = dict(top_common_references)
    summary_graph.node[x]["top_common_references"] = top_common_references


#remove self links from summary graph
  for edge in summary_graph.edges(data = True):
    if edge[0] == edge[1]:
      summary_graph.remove_edge(edge[0], edge[1])


  summary_json = json_graph.node_link_data(summary_graph)

  # giving groups node_names based on size of groups
  for i, n in enumerate(sorted(summary_json["nodes"], key=lambda x:x["paper_count"], reverse=True)):
    for possible_real_index, node in enumerate(summary_json["nodes"]):
      if node == n:
        real_index = possible_real_index 
    summary_json["nodes"][real_index]["node_name"] = i +1


  for i, n in enumerate(summary_json["nodes"]):
    #cache this so graph manipulation later is easier
    summary_json["nodes"][i]["stable_index"] = i
    #find the node

  final_data = {"summaryGraph" : summary_json, "fullGraph" : json_graph.node_link_data(G) }
  return final_data


# Main machinery
def get_papernetwork(solr_data, max_groups, weighted=True, equalization=False, do_cutoff=False):
    '''
    Given a list of bibcodes, this function builds the papers network based on co-citations
    If 'weighted' is true, we will normalize the co-occurence frequency with the total number
    of papers in the set, otherwise we will work with the actual co-occurence frequencies.
    If 'equalization' is true, histogram equalization will be applied to the force values in
    the network
    
    Approach: given a reference dictionary {'paper1':['a','b','c',...], 'paper2':['b','c','g',...], ...}
              we contruct a matrix [[0,1,0,1,...], [0,0,1,...], ...] where every row corresponds with
              a paper in the original paper list and each column corresponds with the papers cited by these
              papers. The paper-citation matrix R is then the transpose of this matrix. The co-occurence
              (paper-paper) matrix is then R_t*R (with R_t the transpose of R). In case we scale with weights,
              represented by a weight matrix W, the scaled co-occurence matrix is R_t*(R-W). Later on we scale
              the force between nodes with a factor proportional to the inverse square root of the product
              of the number of references in the linked nodes.
    '''
    # Get get paper list from the Solr data
    papers_list = map(lambda a: a['bibcode'], solr_data)
    number_of_papers = len(papers_list)
    # First construct the reference dictionary, and a unique list of cited papers
    reference_dictionary = _get_reference_mapping(solr_data)
    
    # From now on we'll only work with publications that actually have references
    papers = reference_dictionary.keys()
    # Compile a unique list of cited papers
    ref_list = list(set([ref for sublist in reference_dictionary.values() for ref in sublist]))
    # transform that list into a dictionary for fast lookup
    ref_list = dict(zip(ref_list, range(len(ref_list))))
    empty_vec = [0]*len(ref_list)
    # Construct the paper-citation occurence matrix R
    entries = []
    for p in papers:
        vec = empty_vec[:]
        ref_ind = map(lambda a: ref_list.get(a), reference_dictionary[p])
        for entry in ref_ind:
            vec[entry] = 1
        entries.append(vec)
    
    #done with ref_list
    ref_list = None
    
    R = mat(entries).T
    # Contruct the weights matrix, in case we are working with normalized strengths
    if weighted:
        lpl = float(len(papers_list))
        weights = []
        for row in R:
            weights.append(array(row) * ((row * row.T / lpl).item()))
        if (len(weights) < 2):
            W = zeros(shape=R.shape)
        else:
            W = numpy.concatenate(weights)
        
        # Note for Edwin, weight elements are suspiciously uniform (does the wighting even have any sense?)
        # they are always filled with 1s - so onen could accomplish the same (on line 214) by doing 1/len(papers)
        
        # this is just an attempt to do it using numpy parallelism, it was actually awfully slow :) maybe you see way to improve it? 
        #diagonal = (R * R.T).diagonal() # these are the weights, because dot product will sum ones (and ignore zeroes)
        #diagonal = diagonal / float(len(papers_list)) # now apply weight
        #weights = diagonal.T * ones(R.shape[1]) # matrix of weights; is there some better way to construct it from the diagonal?
        #W = multiply(R, weights) # now apply weights onto the matrix
        
    else:
        W = zeros(shape=R.shape)
    # Now construct the co-occurence matrix
    # In practice we don't need to fill the diagonal with zeros, because we won't be using it
    C = R.T*(R-W)
    fill_diagonal(C, 0)
    # Compile the list of links
    links = []
    link_dict = {}
    # Can this be done faster? It looks like this could be done via matrix multiplication
    # Don't forget that this is a symmetrical relationship and the diagonal is irrelevant, 
    # so we will only iterate over the upper diagonal. Seems like this could be pulled in
    # the generation of W (above)
    ref_papers = dict(zip(papers, range(len(papers))))
    Npapers = len(papers)
    for i in range(Npapers):
        for j in range(i+1,Npapers):
            scale = sqrt(len(reference_dictionary[papers[i]])*len(reference_dictionary[papers[j]]))
            force = 100*C[ref_papers.get(papers[i]),ref_papers.get(papers[j])] / scale
            if force > 0:
                link_dict["%s\t%s"%(papers[i],papers[j])] = int(round(force))
                link_dict["%s\t%s"%(papers[j],papers[i])] = int(round(force))
    # Cut the list of links to the maximum allowed by first sorting by force strength and then cutting by maximum allowed
    if do_cutoff:
        link_dict = _sort_and_cut_results(link_dict)
    # If histogram equalization was selected, do this and replace the links list
    if equalization:
        links = []
        HE = histeq.HistEq(link_dict)
        link_dict = HE.hist_eq()
    # Now contruct the list of links
    for link in link_dict:
        paper1,paper2 = link.split('\t')
        overlap = reference_dictionary[paper1].intersection(reference_dictionary[paper2])
        force = link_dict[link]
        links.append({'source':ref_papers.get(paper1), 'target': ref_papers.get(paper2), 'value':force, 'overlap':overlap})
    
    
    # Compile node information
    selected_papers = {}.fromkeys(papers)
    nodes = []
    for paper in solr_data:
        if paper['bibcode'] not in selected_papers:
            continue
        nodes.append({'node_name':paper['bibcode'], 
                      'nodeWeight':paper.get('citation_count',1),
                      'citation_count':paper.get('citation_count',0),
                      'read_count':paper.get('read_count',0),
                      'title':paper.get('title','NA')[0],
                      'year':paper.get('year','NA'),
                      'first_author':paper.get('first_author','NA')
                  })
    # That's all folks!
    paper_network = {'nodes': nodes, 'links': links}

    # not quite all...
    return augment_graph_data(paper_network, max_groups)
                