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

import importlib
import random

import method_spec
from test_case_generator import *

###---------------------------------------------------
### TYPE-SPECIFIC PROCESSING:
###---------------------------------------------------
def _process_class(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the class instance
    parameter specified by the inputs.
    """
    ## Recursive case: class!
    class_name, field_types = subtypes[idx]
    class_name, field_vals = subvals[idx]

    ## Extract the names, types, and vals into separate lists
    all_field_names = [field[0] for field in field_types]
    all_field_types = [field[1][0] for field in field_types]
    all_field_vals = [field[1][0] for field in field_vals]

    ## Recursively exhaustively generate values for all fields in this
    ## class object
    field_possible_args = process_types_rec(all_field_types, \
        all_field_vals, variables, PROCESS_FXNS)

    ## Recursively generate all combinations of fields for this 
    ## object; these combinations will in turn serve as all possible 
    ## top-level values for this object's arg
    field_arg_lists = []
    field_idx = 0
    generate_arg_lists(field_possible_args, field_idx, \
        field_arg_lists, variables)

    ## Separate varnames from fields
    possible_varnames = [(arg_list[0],) for arg_list in field_arg_lists]
    field_arg_lists = [arg_list[1] for arg_list in field_arg_lists]

    return list(possible_varnames[0]), field_arg_lists

def _process_int(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the int parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    dummy, dummy2, possible_args = VAR_LOOKUP(possible_vals, variables)
    return [((None, None),)], [random.choice(possible_args)]

def _process_bol(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the bool parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    dummy, dummy2, possible_args = VAR_LOOKUP(possible_vals, variables)
    return [((None, None),)], [random.choice(possible_args)]

def _process_flt(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the float parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    dummy, dummy2, possible_vals = VAR_LOOKUP(possible_vals, variables)

    ## If we have a range of values, generate a random value on that 
    ## continuous spectrum
    if type(possible_vals) == type(xrange(0)):
        val = possible_vals[0] + (random.random() * \
            (possible_vals[-1] - possible_vals[0]))

    ## Otherwise, we have a discrete list of possible values, so choose a
    ## random element from that list
    else:
        val = random.choice(possible_vals)

    return [((None, None),)], [val]

def _process_str(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the str parameter 
    specified by the inputs.
    """
    subtype, keywords = subtypes[idx]

    if type(subvals[idx]) == type(xrange(0)):

        ## Get the character domain
        if not keywords:
            # default to everything
            domain = string.printable

        elif LOWER in keywords:
            domain = string.lowercase

        elif UPPER in keywords:
            domain = string.uppercase

        elif LETTERS in keywords:
            domain = string.letters

        elif DIGITS in keywords:
            domain = string.digits

        elif HEXDIGITS in keywords:
            domain = string.hexdigits

        elif keywords[0][0] == "\"" and keywords[0][-1] == "\"":
            ## Explicit domain as a string of characters
            domain = keywords[0][1:-1]

        else:
            raise ValueError

        ## Randomly select a valid length
        length_range = subvals[idx]
        dummy, dummy2, length_range = VAR_LOOKUP(length_range, variables)
        length = random.choice(length_range)

        ## Generate random one permutation of this length   
        chars = []
        for i in range(length):
            ## Select each character to go in this string
            chars.append(random.choice(domain))
        opts = ["".join(chars)]

    else:
        opts = tuple(subvals[idx])
        dummy, dummy2, opts = VAR_LOOKUP(opts, variables)
        opts = [random.choice(opts)]

    return [((None, None),)], opts

def _process_tup(subtypes, subvals, idx, variables, typestr="tuple"):
    """
    Returns a random choice of possible value for the tuple parameter 
    specified by the inputs. This tuple can be nested arbitrarily deeply.
    """
    subtype, keywords = subtypes[idx]
    length_range = subvals[idx]
    dummy, dummy2, length_range = VAR_LOOKUP(length_range, variables)

    ## Randomly select a valid length
    length = random.choice(length_range)

    ## Get the information about the elements to go in this tuple
    idx += 1
    next_subtype, next_keywords = subtypes[idx]

    if next_subtype in PROCESS_FXNS:
        next_process_fxn = PROCESS_FXNS[next_subtype]
    else:
        next_process_fxn = PROCESS_FXNS[CLASS]

    ## Generate one random permutation of this length   
    arg = []
    while len(arg) < length:
        ## Select each element to go in this tuple
        retval = next_process_fxn(subtypes, subvals, idx, \
            variables)
        next_val = retval[1][0]

        ## Make sure we maintain sorted-ness, if requested
        if (typestr != "set" and SORTED not in keywords) or len(arg) == 0 or \
            (SORTED in keywords and next_val >= arg[-1]) or \
            (typestr == "set" and next_val not in arg):
            arg.append(next_val)
    
    retval = [((None, None),)], [(typestr, tuple(arg))]
    return retval

def _process_lst(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the list parameter 
    specified by the inputs. This list can be nested arbitrarily deeply.
    """
    perm_varnames, perms = _process_tup(subtypes, subvals, idx, variables, \
        "list")
    return perm_varnames, perms

def _process_set(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the set parameter 
    specified by the inputs. This set can be nested arbitrarily deeply.
    """
    perm_varnames, perms = _process_tup(subtypes, subvals, idx, variables, \
        "set")
    return perm_varnames, perms

def _process_dic(subtypes, subvals, idx, variables):
    """
    Returns a random choice of possible value for the dict parameter 
    specified by the inputs. This dict can be nested arbitrarily deeply.
    """
    subtype, keywords = subtypes[idx]
    length_range = subvals[idx]
    dummy, dummy2, length_range = VAR_LOOKUP(length_range, variables)

    ## Randomly select a valid length
    length = random.choice(length_range)

    ## Get the information about the elements to go in this tuple
    idx += 1
    key_subtypes, val_subtypes = subtypes[idx]
    key_subvals, val_subvals = subvals[idx]
    first_key_subtype, first_key_keywords = key_subtypes[0]
    first_val_subtype, first_val_keywords = val_subtypes[0]

    ## Get the processing functions for the keys and values
    if first_key_subtype in PROCESS_FXNS:
        first_key_process_fxn = PROCESS_FXNS[first_key_subtype]
    else:
        first_key_process_fxn = PROCESS_FXNS[CLASS]
    
    if first_val_subtype in PROCESS_FXNS:
        first_val_process_fxn = PROCESS_FXNS[first_val_subtype]
    else:
        first_val_process_fxn = PROCESS_FXNS[CLASS]

    key_list = []
    val_list = []

    ## Generate one random permutation of this length   
    while len(key_list) < length:
        dummy, keys = first_key_process_fxn(key_subtypes, key_subvals, \
            0, variables)
        dummy, vals = first_val_process_fxn(val_subtypes, val_subvals, \
            0, variables)

        ## Only add this key if it's new!
        if keys[0] not in key_list:
            key_list.append(keys[0])
            val_list.append(vals[0]) 

    return [((None, None),)], [("dict", ((tuple(key_list), tuple(val_list)),), \
        ((None, None),))]

## All available type-specific processing functions, for use by the top-level
## parse_types
PROCESS_FXNS = {int:   _process_int,
                set:   _process_set,
                str:   _process_str,
                bool:  _process_bol,
                dict:  _process_dic,
                list:  _process_lst,
                float: _process_flt,
                tuple: _process_tup,
                CLASS: _process_class}

###---------------------------------------------------
### TOP-LEVEL PROCESSING:
###---------------------------------------------------
def generate_random_cases(infile):
    """
    Randomly generate test cases.
    """
    types = CONVERT_TYPES(method_spec.TYPES)

    base_set_path = "base_set_generation.output." + infile.split("/")[-1][:-3]
    base_test_set = importlib.import_module(base_set_path)
    existing_cases = base_test_set.EXHAUSTIVE_CASES[:]

    ## Build randomized cases, one at a time
    randomized_cases = []
    converted_cases = []

    ## Keep going until we've reached the upper bound on the number of 
    ## randomized test cases
    num_attempts = 0
    while len(randomized_cases) < method_spec.RANDOMIZED_BOUND:
        dup = 0
        num_attempts += 1

        ## Pick a value for each variable
        variables = {}
        for varname, varrange in method_spec.VARS.items():
            val = random.choice(varrange)
            variables[varname] = [val]

        ## Randomly generate a new case
        test_case = process_types(method_spec, types, method_spec.RANDOMIZED_VALS,
            variables, PROCESS_FXNS)[0]

        ## Instantiate any classes
        class_converted_args = CONVERT_CLASSES(method_spec, test_case, 
            method_spec.TYPES)

        ## Perform validation; only add this test case if it passes 
        if not method_spec.rvalidation_fxn(class_converted_args):
            continue

        ## Regenerate the non-class version of the test case, in case our
        ## validation function mutated it
        test_case = UNCONVERT_CLASSES(method_spec, class_converted_args,
            method_spec.TYPES)

        ## Only add it if it's a) self-consistent (otherwise 
        ## process_types would've returned None), b) not covered by the 
        ## exhaustive test cases, and c) not already randomly-generated in a 
        ## prior iteration
        if test_case:
            for case in existing_cases:
                if test_case == case:
                    ## Duplicate; try again
                    dup = 1
                    break
            if dup:
                continue

            existing_cases.append(test_case)
            randomized_cases.append(test_case)
            converted_cases.append(class_converted_args)

    return randomized_cases, converted_cases

def gen_write_random_cases(outfile):
    """
    Randomly generate test cases and write the output to a file.
    """
    ## Generate test cases
    test_cases, converted_test_cases = generate_random_cases(outfile)

    ## Write test cases to file
    f = open(outfile, "a")
    f.write("RANDOMIZED_CASES = " + repr(test_cases))
    f.close()

    ## Return the Python object version
    return converted_test_cases
