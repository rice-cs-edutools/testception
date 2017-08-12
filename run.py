#!/usr/bin/python

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

import argparse
import importlib 
import json
import os
import sys

import base_set_generation.config_file_parser as cfp
import extractor
import progression_scheduler
import tester
from base_set_generation.test_case_generator import CONVERT_CLASSES

def update_menu(): 
    """
    Implementation of updatemenu command; this command should be run every 
    time you change the contents of the project folder.

    Updates all project information, including project name list and project 
    function lists. Displays updated menu.
    """
    ## json format: {project_index: {"projname": name, 
    ##                               "funclist": [list of functions]}, ... } 
    menu = {} 
    index = {}   
    projects = os.listdir("projects")
    projnos = []

    ## Validate contents of projects directory to ensure that subdirectories
    ## meet specifications. Subdirectories must be named in the form 
    ## "projectX", where X is an integer.
    for dirname in projects:
        if dirname.startswith("project"):
            try:
                dirnum = int(dirname[7:])
            except:
                print " ERROR: skipping projects/" + dirname
                print "\tSubdirs must be named \"projectX\", where X is an" \
                     + " integer.\n"
                continue

            projnos.append(int(dirnum))

        elif dirname == "examples":
            continue

        else:
            print " ERROR: skipping projects/" + dirname
            print "\tSubdirs must be named \"projectX\", where X is an integer.\n"

    ## Construct menu based on contents of projects directory
    offset = 0
    for ind in projnos: 
        sys.path.insert(0, os.getcwd() + "/projects/project" + str(ind))
        if not "info" in dir():
            try:
               info = importlib.import_module("description")
               sys.path.pop(0) 
            except:
                print " ERROR: skipping projects/project" + str(ind)
                print "\tMissing description.py.\n"
                continue
        else: 
            info = reload(info)
        menu[ind] = {}
        menu[ind]["projname"] = info.projectname
        menu[ind]["funclist"] = info.funclist

    ## Save menu to file, for easy access via showmenu
    f = open("menu.json", "w") 
    json.dump(menu, f)
    f.close()

    ## Display updated menu
    showmenu()

def showmenu(): 
    """
    Display menu, as stored in menu.json.
    """
    try:
       f = open("menu.json")
       menu = json.load(f)
       f.close()
    except:
        print " ERROR: run updatemenu to generate updated menu"
        return

    for ind in sorted([int(i) for i in menu.keys()]):
        projname = menu[str(ind)]["projname"]
        print " " + str(ind) + ": " + projname
        for no, func in enumerate(menu[str(ind)]["funclist"]):
            print "   |" 
            print "   --- " + str(no) + ": " + func
        print 
  
def extract_files(projno, funcno, studentdir):
    """
    Extract function(s) from files. If funcno < 0, extracts all functions from
    the given project.
    """
    cwd = os.getcwd()
    sys.path.insert(0, cwd + "/projects/project" + str(projno))
    info = importlib.import_module('description')
    ## Remove the path to avoid keeping old paths
    sys.path.pop(0)
    
    if funcno < 0:
        numfuncs = len(info.funclist)
        funcnos = range(numfuncs)
    else:
        funcnos = [funcno]

    outputdir = cwd + "/extracted_files/proj" + str(projno) + "_func"
    funcnames = [info.funclist[int(fno)] for fno in funcnos]

    extractor.main(os.path.abspath(studentdir), outputdir, funcnos, 
        funcnames) 

def gen_base_test_set(projno, funcno, importdir=None):
    """
    Generates the base test cases for the specified (problem, function).
    """
    cwd = os.getcwd()
    outpath = cwd + "/base_set_generation/output/proj" + str(projno) + "_func" \
        + str(funcno) + ".py"
    ms_outpath = cwd + "/base_set_generation/output/ms_proj" + str(projno) + "_func" \
        + str(funcno) + ".py"

    ## Parse the appropriate confid file and auto-generate method_spec.py
    try:
        cfp.parse_config_file(projno, funcno, ms_outpath, importdir)
    except:
        raise
        print " ERROR: failed to parse config file; please see " \
            + "./projects/examples for\n    examples of valid config files, and " \
            + "README for a complete specification of\n    the config file grammar"
        return -1

    ## These can't happen up top because they import method_spec, which is 
    ## generated by parse_config_file()
    try:
        import base_set_generation.exhaustive_generator as egen
        import base_set_generation.randomized_generator as rgen
    except ImportError as ex:
        ## Validation file not found
        print " ERROR:", ex.message
        return -1

    ## Generate the exhaustive test cases
    exhaustive_cases = egen.gen_write_exhaustive_cases(outpath)

    ## Generate the randomized test cases
    randomized_cases = rgen.gen_write_random_cases(outpath)

    ## Return the concatenation of the two sets of test cases
    return exhaustive_cases + randomized_cases

def main():
    """ 
    Execute command. See README (or use -h) for options.
    """ 
    ## Create an argument parser 
    parser = argparse.ArgumentParser(add_help=False)

    ## cmd = [ updatemenu | showmenu | extract | gen | test | pick | all ]
    sp = parser.add_subparsers()
    subparsers = {}

    CMD = "updatemenu"
    sp_update = sp.add_parser(CMD, 
        help="update the menu of project/function options")
    sp_update.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_update, [])
       
    CMD = "showmenu"
    sp_show = sp.add_parser(CMD, 
        help="show the menu of project/function options")
    sp_show.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_show, [])

    CMD = "extract"
    sp_extract = sp.add_parser(CMD, help="extract implementations from files")
    sp_extract.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_extract, ["p", "f", "s", "i"])

    CMD = "gen"
    sp_gen = sp.add_parser(CMD,  help="generate base test set")
    sp_gen.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_gen, ["p", "f", "i"])

    CMD = "test"
    sp_test = sp.add_parser(CMD, help="test extracted implementations")
    sp_test.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_test, ["p", "f", "i"])

    CMD = "pick"
    sp_pick = sp.add_parser(CMD, 
        help="determine progression through implementations")
    sp_pick.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_pick, ["p", "f", "i"])

    CMD = "all"
    sp_all = sp.add_parser(CMD, help="extract && gen && test && pick")
    sp_all.set_defaults(cmd=CMD)
    subparsers[CMD] = (sp_all, ["p", "f", "s", "i"])

    ## Set up sub-arguments for non-menu commands
    for cmd, (subp, sub_cmds) in subparsers.items():
        args = subp.add_argument_group(title="required arguments")

        if "p" in sub_cmds:
            args.add_argument("-p", "--projno", type=int,
                help="project index (from menu)")
        if "f" in sub_cmds:
            args.add_argument("-f", "--funcno", type=int, 
                help="function index (from menu)")
        if "s" in sub_cmds:
            args.add_argument("-s", "--student-dir", type=str,
                help="directory containing student solutions")
        if "i" in sub_cmds:
            args.add_argument("-i", "--import-dir", type=str,
                help="directory containing provided files")

    ## Extract args
    try:
        args = parser.parse_args()
        cmd = args.cmd
        subp, sub_cmds = subparsers[cmd]

        if ("p" in sub_cmds and args.projno == None) or \
            ("f" in sub_cmds and args.funcno == None) or \
            ("s" in sub_cmds and args.student_dir == None):
            subp.print_help()
            return

    except:
        parser.print_help()
        return

    ## Add provided module path to sys.path, so that files can import 
    ## provided modules directly
    if "i" in sub_cmds and args.import_dir:
        sys.path.insert(0, os.path.abspath(args.import_dir))

    ## Call proper function(s) according to cmd 
    if cmd == "updatemenu": 
        update_menu() 
        return

    elif cmd == "showmenu":
        showmenu()
        return

    try:
       f = open("menu.json")
       menu = json.load(f)
       f.close()
    except:
        print " ERROR: run updatemenu to generate updated menu"
        return

    cwd = os.getcwd()
    config_file_path = cwd + "/projects/project" + str(args.projno) + "/func" \
        + str(args.funcno) + ".cfg"
    if not os.path.exists(config_file_path):
        print " ERROR: file " + config_file_path + " does not exist"
        return

    if cmd == "extract":
        print " * Extracting programs from files..."
        print
        extract_files(args.projno, args.funcno, args.student_dir)
        print " Done!\n"

    elif cmd == "gen":
        print " * Generating base test set..."
        base_test_set = gen_base_test_set(args.projno, args.funcno, args.import_dir)
        if base_test_set == -1:
            print " Generation failed."
            return
        print " Done!\n"

    elif cmd == "test":
        ## Attempt to reload base test set from previous generation
        try:
            base_set_path = "base_set_generation.output.proj" \
                + str(args.projno) + "_func" + str(args.funcno)
            method_spec_path = "base_set_generation.output.ms_proj" \
                + str(args.projno) + "_func" + str(args.funcno)
            bts_mod = importlib.import_module(base_set_path)
            ms_mod = importlib.import_module(method_spec_path)

            os.remove(os.path.abspath("./base_set_generation/output/proj" \
                + str(args.projno) + "_func" + str(args.funcno) + ".pyc"))
            reload(bts_mod)
            os.remove(os.path.abspath("./base_set_generation/output/ms_proj" \
                + str(args.projno) + "_func" + str(args.funcno) + ".pyc"))
            reload(ms_mod)

            ## If there are class objects, instantiate them
            base_test_set = bts_mod.EXHAUSTIVE_CASES + bts_mod.RANDOMIZED_CASES
            base_test_set = [CONVERT_CLASSES(ms_mod, case, ms_mod.TYPES) \
                for case in base_test_set]

        except:
            raise
            print " ERROR: run gen to generate base test set"
            return
        
        print " * Identifying bugs..."
        retval = tester.run_tests(args.projno, args.funcno, base_test_set, 
            args.import_dir)
        if retval == -1:
            print " Bug identification failed."
            return
        print " Done!\n"

    elif cmd == "pick":
        print " * Scheduling progression..."
        progression_scheduler.pick_programs(args.projno, args.funcno, 
            args.import_dir)
        print " Done!\n"

    elif cmd == "all":
        print " * Extracting programs from files..."
        retval = extract_files(args.projno, args.funcno, args.student_dir)
        if retval == -1:
            print " Extraction failed."
            return

        print " * Generating base test set..."
        base_test_set = gen_base_test_set(args.projno, args.funcno, args.import_dir)
        if base_test_set == -1:
            print " Base test set generation failed."
            return

        print " * Identifying bugs..."
        retval = tester.run_tests(args.projno, args.funcno, base_test_set, 
            args.import_dir)
        if retval == -1:
            print " Bug identification failed."
            return 

        print " * Scheduling progression..."
        progression_scheduler.pick_programs(args.projno, args.funcno, 
            args.import_dir) 
        print " Done!\n"

    else: 
        parser.print_help()

if __name__ == "__main__":
    main()
