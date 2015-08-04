import string

def get_total_memory(query, rows):
    f = open("memory_profiler_{0}_{1}.txt".format(query, rows))
    total_memory = 0
    for line in list(f):
        data = string.split(line)
        try:
            total_memory += float(data[3])
        except (IndexError, ValueError):
            pass
    f.close()
    return total_memory
    
def get_line_memory(query, rows, line):
    f = open("memory_profiler_{0}_{1}.txt".format(query, rows))
    line_memory = 0
    for line in list(f):
        data = string.split(line)
        if int(data[0]) == line:
            try:
                line_memory = float(data[3])
            except (IndexError, ValueError):
                print "Error: Choose a different line."
    f.close()
    return line_memory
