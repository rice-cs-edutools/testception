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

import copy 
import errno
import importlib
import json
import multiprocessing
import os
import pickle
import sys
import datetime

from progress.bar import ChargingBar

from utils.deep_equal import deep_equal

def run_tests(projno, funcno, test_set, importdir):
    """
    Execute test_set on extract files for given (projno, funcno).
    """
    starttime = datetime.datetime.now()
    inputdir = os.getcwd() + "/extracted_files/proj" + str(projno) + "_func" \
        + str(funcno)

    ## Remove *.pyc
    try:
        filelist = os.listdir(inputdir)
    except:
        print " ERROR: missing corpus; please run extract or manually " \
            + "populate directory\n    " + inputdir
        return -1

    for fname in filelist:
        if fname[-4:] == ".pyc":
            os.system("rm {0}/{1}".format(inputdir, fname))
    filelist = os.listdir(inputdir)

    ## Enable importing programs from corpus (and importing provided files)
    sys.path.insert(0, inputdir)
    files = os.listdir(inputdir)
    num_files = len(files)
    if importdir:
        sys.path.insert(0, os.path.abspath(importdir))

    ## Add problem folder path into sys path so that we can import the 
    ## solution module
    sys.path.insert(0, os.getcwd()+ "/projects/project" + str(projno))
    solution = importlib.import_module("solution")

    ## Instantiate tester
    with open("menu.json") as data_file:
        menu = json.load(data_file)
    funcname = menu[str(projno)]["funclist"][funcno]
    tester = Tester(solution, funcname, test_set)

    if len(tester.case_map) == 0:
        print " ERROR: base test set is empty; please check that the domain " \
            + "is non-empty\n    and validation function accepts a subset of " \
            + "that domain"
        return -1

    try:
        case = tester.case_map[0]
        temp_case = copy.deepcopy(case)
        ref_func = getattr(solution, funcname)
        ref_result = ref_func(*temp_case)
    except:
        raise
        print " ERROR: failed while testing reference solution; please check" \
            + " that\n    the solution is correct and that its parameters" \
            + " match the\n    specification in the config file"
        return -1

    tester.solution_results()

    ## Prepare to output test results
    try:
        os.makedirs(os.getcwd() + "/test_output")
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise
    fout = file("./test_output/files_proj" + str(projno) + "_func" \
        + str(funcno) + ".txt", "w+")
    bar = ChargingBar("   -- Running base test set on corpus", max=num_files)

    ## Test all programs
    count = 0
    for fname in filelist:
        bar.next()
        fout.write("\nFile {0}: {1}".format(count, fname))
        fout.flush()

        ## Load student submission for testing; catch import exceptions
        try:
            submission = importlib.import_module(fname[:-3])
        except:
            tester.remove_set.add(fname)
            count += 1
            continue

        ## Test submission on base test set
        tester.test_fast(submission, fname, count)
        count += 1

    bar.finish()
    fout.close()

    try:
        ## Save the results in the ./test_output directory, for use by the
        ## progression scheduler
        tester.sol = None ## Can't pickle module objects
        results_filename = "./test_output/proj" + str(projno) + "_func" \
            + str(funcno) + ".pickle"
        if os.path.isfile(results_filename):
            os.system("rm {0}".format(results_filename))
        f_results = open(results_filename, "w+")
        pickle.dump(tester, f_results)

    except:
        print " ERROR: failed to dump test results to pickle file"
        return -1

    endtime = datetime.datetime.now()
    print "      Correct:", len(tester.correct_set)
    print "      Incorrect:", len(tester.wrong_set)
    print "      Runtime:", endtime - starttime
    print

def test_helper_fast(submission, funcname, case_map, results, queue):   
    """
    Helper function for testing a student submission; results are returned
    via queue.
    """
    test_func = getattr(submission, funcname)
    test_flag = True
    keys = case_map.keys()
    keyslen = len(keys)

    processedkeys = []
    wronginds = []

    for i in range(keyslen):
        ind = keys[i]
        case = case_map[ind] 

        temp_case = copy.deepcopy(case)
        ref_result = results[ind]
        correctness_flag = False
        try: 
            test_result = test_func(*temp_case)
            if not deep_equal(ref_result, test_result, float_tol=1e-5):
                correctness_flag = False
            else: 
                correctness_flag = True
        except: 
            correctness_flag = False

        if not correctness_flag: 
            wronginds.append(ind)
            test_flag = False

    queue.put(wronginds)
    queue.put(test_flag)

def ref_helper_fast(solution, funcname, test_case, queue):   
    """
    Helper function for testing the reference solution; results are returned
    via queue.
    """
    ref_func = getattr(solution, funcname)
    ref_result = ref_func(*test_case)
    queue.put(ref_result)
    
class Tester():
    """
    Class used to execute base test cases.
    """
    def __init__(self, solution, funcname, test_set):
        ## Reference solution (correct implementation)
        self.sol = solution

        ## Function to be tested
        self.funcname = funcname

        ## Base test set 
        self.base_set = test_set

        ## Testing results
        self.results = {}

        ## Mapping of {test_case_index: set([files that failed this test])}
        self.case_file = {}  

        ## Mapping of {file_name: set([test cases indices it failed on])}
        self.file_case = {}

        self.wrong_set = set()
        self.correct_set = set()
        self.remove_set = set()
        self.timeoutlimit = 15

        ## Assigns an explicit index to each case; easier than using the list 
        ## indices for the purposes of multiprocessing
        self.create_case_map()

    def create_case_map(self):
        """
        Enable test case lookup using index,  {index: case, ... }  
        """
        self.case_map = {}
        for ind, case in enumerate(self.base_set):
            self.case_map[ind] = case

    def solution_results(self):
        """
        Generates the results of all test cases and stores in self.results.
        """
        bar = ChargingBar("   -- Generating reference results ",
            max=len(self.base_set))

        for ind in range(len(self.base_set)):
            bar.next()
            case = self.case_map[ind]
            temp_case = copy.deepcopy(case)

            queue = multiprocessing.Manager().Queue()

            ## Start correctness checker as a subprocess
            p = multiprocessing.Process(target=ref_helper_fast, \
                args=(self.sol, self.funcname, temp_case, queue))
            p.start()

            ## Wait for self.timeout seconds or until process finishes
            p.join(self.timeoutlimit)

            ## If thread is still active, kill it and return 
            if p.is_alive():
                p.terminate()
                p.join()
                print "\nTimeout when testing ref_func(" \
                    + str(temp_case) + ")\n"
                continue

            self.results[ind] = queue.get()

        bar.finish()

    def update_file_case(self, fname, ind):
        if not fname in self.file_case: 
            self.file_case[fname] = set()
        self.file_case[fname].add(ind)

    def update_case_file(self, ind, fname):
        if not ind in self.case_file: 
            self.case_file[ind] = set()
        self.case_file[ind].add(fname)

    def test_fast(self, submission, fname, findex):
        """
        Tests the correctness of the given student submission.
        """
        try:
            test_func = getattr(submission, self.funcname)
        except:
            self.remove_set.add(fname)
            return

        ## Correctness flag for submission
        correctness_flag = True 

        ## Use queue to hold results
        queue = multiprocessing.Manager().Queue()

        ## Start correctness_checker as a subprocess
        self.file_case[findex] = set()
        p = multiprocessing.Process(target=test_helper_fast,
            args=(submission, self.funcname, self.case_map, self.results, 
            queue))
        p.start()

        ## Wait for self.timeout seconds or until process finishes
        p.join(self.timeoutlimit)

        ## If thread is still active, kill it and return 
        if p.is_alive():
            p.terminate()
            p.join()
            self.remove_set.add(fname)
            return 

        ## Process test case failures
        wronginds = queue.get()
        for ind in wronginds:
            self.update_file_case(findex, ind)
            self.update_case_file(ind, findex)

        ## Classify this submission as correct or buggy
        correctness_flag = queue.get() 
        if not correctness_flag:
            self.wrong_set.add(findex)
        else: 
            self.correct_set.add(findex)
