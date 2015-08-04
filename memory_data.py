from memory_parser import get_total_memory, get_line_memory
import matplotlib.pyplot as plt
from sys import argv
from get_papernetwork_totalref import get_unique_references, get_matrix_size

script, query = argv

def plot_one():
    row_range = range(0, 1000, 50)
    print "What graph would you like?"
    print "1: Memory in terms of rows."
    print "2: Memory in terms of unique references."
    print "3: Unique references in terms of rows."
    graph = raw_input("[Type 1, 2, or 3]: ")
    ylist = []
    if graph == "1":
        xlist = row_range
        plt.xlabel("Rows")
        ylist = plot_memory(ylist, row_range)
        plt.ylabel("Memory (Megabytes)")
    elif graph == "2":
        xlist = []
        for row in row_range:
            xlist.append(get_unique_references(query, row))
            plt.xlabel("Unique References")
        ylist = plot_memory(ylist, row_range)
        plt.ylabel("Memory (Megabytes)")
    elif graph == "3":
        xlist = row_range
        plt.xlabel("Rows")
        for row in row_range:
            ylist.append(get_unique_references(query, row))
            plt.ylabel("Unique References")
    else:
        print "Error! Press 1, 2, or 3!"
        plot()
    plt.plot(xlist, ylist, "black")
    plt.show()

def plot_memory(ylist, row_range):
    for x in row_range:
        ylist.append(get_total_memory(query, x))
    return ylist
    
def plot_all():
    row_range = range(0, 1000, 50)
    memlist = []
    memlist = plot_memory(memlist, row_range)
    ref_num_list = []
    matrix_list = []
    for row in row_range:
        ref_num_list.append(get_unique_references(query, row))
        matrix_list.append(get_matrix_size(query, row))
    plt.figure(1)
    plt.xlabel("Rows")
    plt.ylabel("Memory (Megabytes)")
    plt.plot(row_range, memlist, "black")
    plt.figure(2)
    plt.xlabel("Unique References")
    plt.ylabel("Memory (Megabytes)")
    plt.plot(ref_num_list, memlist, "black")
    plt.figure(3)
    plt.xlabel("Rows")
    plt.ylabel("Unique References")
    plt.plot(row_range, ref_num_list, "black")
    plt.figure(4)
    plt.xlabel("Matrix Size")
    plt.ylabel("Memory (Megabytes)")
    plt.plot(matrix_list, memlist, "black")
    plt.show()
plot_all()
