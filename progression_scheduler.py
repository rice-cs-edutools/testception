"""
Copyright 2015-2017 Rebecca Smith, Terry Tang, Joe Warren, and Scott Rixner

This file is part of Testception.

Testception is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later 
version.

Testception is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
Testception. If not, see <http://www.gnu.org/licenses/>.
"""

import errno
import gc 
import hashlib
import importlib
import json
import multiprocessing
import os
import pickle
import sys
import time 

from radon.raw import analyze
from radon.metrics import mi_visit
from radon.complexity import cc_visit

## Cutoff number of programs that share the same signature below which we will 
## throw out the signature as too obscure
MIN_SIGNATURE_SIZE = 1

## Cutoff runtime, in seconds (don't want to pick functions that will cause
## the tester to timeout)
MAX_RUNTIME_S = 37

## Cutoff number of tests a program must have failed to be selected (may not
## want to choose programs that failed on very few)
MIN_NUM_FAILED = 1

## Number of programs to display for a given signature
PROGRAMS_TO_DISPLAY = 3

def load_pickle(projno, funcno, importdir):
    """
    Load the pickled test results for the specified function.
    Requires that ./run.py test <projno> <funcno> was run previously.
    """
    ## Submissions may require some provided modules
    if importdir:
        sys.path.insert(0, os.path.abspath(importdir))
    sys.path.insert(0, os.getcwd()+ "/projects/project" + str(projno))
    solution = importlib.import_module("solution")

    ## Grab the test results
    try:
        f_results = open(os.getcwd() + "/test_output/proj"+ str(projno) \
            + "_func" + str(funcno) + ".pickle")
    except:
        print " ERROR: must execute ./run.py test prior to ./run.py pick"
        return

    tester = pickle.load(f_results)
    gc.collect()
    return tester

def get_monitor(projno, funcno, tester):
    """
    Helper function which builds data structures used by pick_programs.
    """
    file_case = tester.file_case 
    total = len(tester.case_map.keys())

    ## Build mappings of signature to files that share that signature
    monitor = {}
    hashmonitor = {}

    for findex in file_case.keys():
        keystring = json.dumps(list(file_case[findex]))
        key = hashlib.sha224(keystring).hexdigest()
        if key in monitor.keys():
            monitor[key].add(findex)
        else:
            monitor[key] = set([findex])
            hashmonitor[key] = tuple(file_case[findex])
            for ind in tuple(file_case[findex]):
                temptuple = tuple(tester.case_map[ind])

    ## Retrieve the correct and incorrect program sets from base testing
    f = open(os.getcwd() \
        + "/test_output/files_proj{0}_func{1}.txt".format(projno, funcno))
    lines = f.readlines()
    f.close()

    ## Store all filenames in order
    allfilelist = [] 
    for i in range(len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        ind = line.index(":") + 2  
        if line[-1] == "\n":
            allfilelist.append(line[ind:-1])
        else:
            allfilelist.append(line[ind:])  
 
    return len(tester.case_map.keys()), monitor, hashmonitor, allfilelist

def program_complexity(projno, funcno):
    """
    Builds and returns two dictionaries mapping filename:cc and filename:mi.
    """
    cc_dic = {}
    mi_dic = {}

    path = os.getcwd() + \
        "/extracted_files/proj{0}_func{1}/".format(projno, funcno)
    for fname in os.listdir(path):
        if fname[-4:] == '.pyc': continue
        try: 
            f = open(path + fname)
            content = f.read()
            blocks = cc_visit(content)
            mi = mi_visit(content, True)
            cc_dic[fname] = blocks[0].complexity
            mi_dic[fname] = mi
            f.close()

        except:
            print " ERROR: cannot find file " + path + fname

    return cc_dic, mi_dic

def program_length(projno, funcno):
    """
    Builds and returns a dictionary mapping filename:length.
    """
    lengthdic = {}

    path = os.getcwd() + \
        "/extracted_files/proj{0}_func{1}/".format(projno, funcno)
    for fname in os.listdir(path):
        if fname[-4:] == '.pyc': 
            continue
        try: 
            f = open(path + fname)
            lines = f.readlines()
            lengthdic[fname] = len(lines)
            f.close()
        except:
            print " ERROR: cannot find file " + path + fname
    
    return lengthdic

def pick_programs(projno, funcno, importdir):
    """
    For the given function, schedule the progression through implementations.
    """
    ## Generate mappings of {filename: funclen} and {filename: complexity}
    lengthdic = program_length(projno, funcno)
    cc_dic, mi_dic = program_complexity(projno, funcno)

    tester = load_pickle(projno, funcno, importdir)
    if not tester: 
        ## Error loading pickle file
        return

    num_test_cases, monitor, hashmonitor, allfilelist = get_monitor(projno, 
        funcno, tester)

    i = 0
    num_correct_cases = []
    failed_test_cases = []
    fxn_bodies = []
    fxn_names = [] 

    ## Pick candidates for each test signature 
    for key in monitor.keys():
        signature_size = len(monitor[key])

        ## Avoid signatures that are very uncommon
        if signature_size >= MIN_SIGNATURE_SIZE:
            candidatelist = list(monitor[key])
            num_failed = len(hashmonitor[key])

            ## Avoid those failed on very few test cases; those programs will 
            ## frustrate students
            if num_failed >= MIN_NUM_FAILED:
                bodies = []
                names = []
                num_correct_cases.append(num_test_cases - num_failed)

                ## Sort the candidate programs according to the desired metric
                ## to be minimized (e.g. length, complexity, maintainability)
                candidatelist = dict_sort(allfilelist, candidatelist, lengthdic)
                picked = 0
                for candidate in candidatelist:
                    if picked == PROGRAMS_TO_DISPLAY:
                        break

                    start_time = time.time()
                    test_flag = test_candidate(projno, funcno, 
                        allfilelist[candidate], tester.base_set)
                    duration = time.time() - start_time
                    if test_flag and duration < MAX_RUNTIME_S: 
                        f = open(os.getcwd() + "/extracted_files/proj" \
                            + str(projno) + "_func" + str(funcno) + "/" \
                            + allfilelist[candidate])
                        lines = f.readlines()
                        f.close()
                        bodies.append("".join(lines))
                        names.append(allfilelist[candidate])
                        picked += 1

                fxn_names.append(names)
                fxn_bodies.append(bodies)

        i += 1

    ## Sort the programs in descending test signature length
    indexlist = sorted(range(len(num_correct_cases)), 
        key=num_correct_cases.__getitem__)
    count = 0

    ## Output results to ./output/proj<projno>_func<funcno>.py
    try:
        os.makedirs(os.getcwd() + "/output")
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise

    f = open("./output/proj{0}_func{1}.py".format(projno, funcno), "w+")
    f.write("funcs = [")
    for ind in indexlist:
        count += 1
        fnames = fxn_names[ind]
        bodies = fxn_bodies[ind]

        f.write("[")
        for ind2 in range(len(fnames)):
            f.write(json.dumps(bodies[ind2]))
            if ind2 < len(fnames) - 1:
                f.write(",")

        f.write("]")
        if count < len(indexlist):
            f.write(",")

    f.write("]")
    f.close()

def dict_sort(allfilelist, candidatelist, dic):
    """
    Helper function for sorting a list of programs based on a property,
    where dic contains a mapping of program: value for that property.
    """
    lst = []
    for findex in candidatelist: 
        lst.append(dic[allfilelist[findex]])
    indexlist = sorted(range(len(lst)),key=lst.__getitem__)
    ret = []
    for i in indexlist:
        ret.append(candidatelist[i])
    return ret

def test_helper_fast(submission, funcname, test_set):   
    """
    Helper function for running the test_set on a single submission.
    """
    test_func = getattr(submission, funcname)
    for case in test_set:
        temp_case = case
        try: 
            test_result = test_func(*temp_case)
        except: 
            pass

def test_candidate(projno, funcno, fname, test_set): 
    """
    Test the function in fname on the given test_set.
    """
    sys.path.append(os.getcwd() + "/projects/project{0}".format(projno))
    sys.path.insert(0, os.getcwd() \
        + "/extracted_files/proj{0}_func{1}/".format(projno, funcno))
    import description
    funcname = description.funclist[funcno]

    ## Load student submission module for testing 
    if "submission" in dir(): 
        exec("del submission")

    ## Catch import exceptions
    try: 
        submission = importlib.import_module(fname[:-3])
    except: 
        print " ERROR: failed to import file", fname
        return False

    ## Test submission on base test set
    try:
        test_func = getattr(submission, funcname)
    except:
        print " ERROR: unable to extract function from file", fname
        return False

    ## Start correctness_checker as a subprocess
    p = multiprocessing.Process(target=test_helper_fast, 
        args=(submission, funcname, test_set))
    p.start()

    ## Wait for self.timeout seconds or until process finishes
    p.join(45)

    ## If thread is still active, kill it and return 
    if p.is_alive():

        ## Terminate
        p.terminate()
        p.join()
        return False
    else: 
        return True
