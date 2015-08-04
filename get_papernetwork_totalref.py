import numpy
from app import create_app
import unittest
import json

def run(data):
            # get_bibref_data(data)
            bibref_data = {}
            for paper in data:
                if paper.get("reference") is not None:
                    bibref_data[paper.get("bibcode")] = paper.get("reference")
            # get_reference_unique_list(bibref_data)
            reference_list = []
            for l in bibref_data.values():
                for i in l:
                    reference_list.append(i)
            reference_unique_list = list(set(reference_list))
            # get_paper_ref_matrix(bibref_data)
            paper_ref_matrix = []
            for key in bibref_data.keys():
                matrix_row = []
                for reference in reference_unique_list:
                    if reference in bibref_data[key]:
                        matrix_row.append(1)
                    else:
                        matrix_row.append(0)
                paper_ref_matrix.append(matrix_row)
            matrix = numpy.matrix(paper_ref_matrix)
            # cooccurrance_matrix(matrix)
            numpy.set_printoptions(threshold='nan')
            C = matrix*matrix.T
            numpy.fill_diagonal(C, 0)
            return C
            #return cooccurrance_matrix(get_paper_ref_matrix(bibref_data))
            
app = create_app()
def get_unique_references(query, rows):
    r = app.test_client().get("/paper-network?q={0}&rows={1}".format(query, rows))
    data = json.loads(r.data)
    with app.app_context():
        # get_bibref_data(data)
        bibref_data = {}
        for paper in data:
            if paper.get("reference") is not None:
                bibref_data[paper.get("bibcode")] = paper.get("reference")
        # get_reference_unique_list(bibref_data)
        reference_list = []
        for l in bibref_data.values():
            for i in l:
                reference_list.append(i)
        reference_unique_list = list(set(reference_list))
        return len(reference_unique_list)
        #return cooccurrance_matrix(get_paper_ref_matrix(bibref_data))


def get_matrix_size(query, rows):
    r = app.test_client().get("/paper-network?q={0}&rows={1}".format(query, rows))
    data = json.loads(r.data)
    with app.app_context():
        # get_bibref_data(data)
        bibref_data = {}
        for paper in data:
            if paper.get("reference") is not None:
                bibref_data[paper.get("bibcode")] = paper.get("reference")
        # get_reference_unique_list(bibref_data)
        reference_list = []
        for l in bibref_data.values():
            for i in l:
                reference_list.append(i)
        reference_unique_list = list(set(reference_list))
        # get_paper_ref_matrix(bibref_data)
        paper_ref_matrix = []
        for key in bibref_data.keys():
            matrix_row = []
            for reference in reference_unique_list:
                if reference in bibref_data[key]:
                    matrix_row.append(1)
                else:
                    matrix_row.append(0)
            paper_ref_matrix.append(matrix_row)
        matrix = numpy.matrix(paper_ref_matrix)
        return matrix.size    
        #return cooccurrance_matrix(get_paper_ref_matrix(bibref_data))

