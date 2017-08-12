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

import method_spec
from test_case_generator import *

###---------------------------------------------------
### TYPE-SPECIFIC PROCESSING:
###---------------------------------------------------
def _process_class(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the class instance
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
    possible_varnames = [arg_list[0] for arg_list in field_arg_lists]
    field_arg_lists = [arg_list[1] for arg_list in field_arg_lists]
    return possible_varnames, field_arg_lists

def _process_int(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the int parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    varname, varrange, possible_args = VAR_LOOKUP(possible_vals, variables)
    dummy, possible_varnames = POSSIBLE_VARNAMES(varname, varrange, \
        possible_args)
    return possible_varnames, possible_args

def _process_bol(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the bool parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    varname, varrange, possible_args = VAR_LOOKUP(possible_vals, variables)
    dummy, possible_varnames = POSSIBLE_VARNAMES(varname, varrange, \
        possible_args)
    return possible_varnames, possible_args

def _process_flt(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the float parameter 
    specified by the inputs.
    """
    ## Primitive type + no valid keywords (yet), so ignore subtypes
    possible_vals = subvals[idx]
    varnames, varrange, possible_vals = VAR_LOOKUP(possible_vals, variables)

    ## Note that we can't truly be "exhaustive", since there are infinite
    ## possibilities, so for now I'm just using floats of all ints in the
    ## range; random_generation should take care of the other cases
    possible_vals = [float(f) for f in possible_vals]
    dummy, possible_varnames = POSSIBLE_VARNAMES(varnames, varrange, \
        possible_vals)
    return possible_varnames, possible_vals

def _process_str(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the str parameter 
    specified by the inputs.
    """
    subtype, keywords = subtypes[idx]

    if type(subvals[idx]) == type(xrange(0)):

        ## Get the character domain
        if not keywords:
            ## Default to everything
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

    ## Get all permutations of these characters within the specified range
    ## of lengths
        length_range = subvals[idx]
        varname, varrange, length_range = VAR_LOOKUP(length_range, variables)
        max_length = length_range[-1]
        min_length = length_range[0]
        perms = _create_str_perms(max_length, min_length, domain)
        opts = perms.keys()

    else:
        opts = tuple(subvals[idx])
        varname, varrange, opts = VAR_LOOKUP(opts, variables)

    dummy, possible_varnames = POSSIBLE_VARNAMES(varname, varrange, opts, \
        lambda x: len(x))
    return possible_varnames, opts

def _process_tup(subtypes, subvals, idx, variables, typestr="tuple"):
    """
    Returns an exhaustive list of possible values for the tuple parameter 
    specified by the inputs. This tuple can be nested arbitrarily deeply.
    """
    subtype, keywords = subtypes[idx]
    length_range = subvals[idx]
    varname, varrange, length_range = VAR_LOOKUP(length_range, variables)
    base_varname, possible_varnames = POSSIBLE_VARNAMES(varname, varrange, \
        length_range)

    idx += 1
    next_subtype, next_keywords = subtypes[idx]

    ## Get the processing function for the elements within this tuple
    if next_subtype in PROCESS_FXNS:
        next_process_fxn = PROCESS_FXNS[next_subtype]
    else:
        next_process_fxn = PROCESS_FXNS[CLASS]

    ## Get the list of all potential elements of this tuple
    nested_varnames, next_vals = next_process_fxn(subtypes, subvals, idx, \
        variables)

    ## Get all permutations of the possible next_vals within the specified 
    ## range of lengths 
    max_length = length_range[-1]
    min_length = length_range[0]
    perms, perm_varnames = _create_tup_perms(max_length, min_length, \
        base_varname, varrange, next_vals, nested_varnames, keywords, \
        varname, typestr)
    perms = [(perm[0], perm[1]) for perm in perms]

    return perm_varnames, perms

def _process_lst(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the list parameter 
    specified by the inputs. This list can be nested arbitrarily deeply.
    """
    perm_varnames, perms = _process_tup(subtypes, subvals, idx, variables, \
        "list")
    return perm_varnames, perms

def _process_set(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the set parameter 
    specified by the inputs. This set can be nested arbitrarily deeply.
    """
    perm_varnames, perms = _process_tup(subtypes, subvals, idx, variables, \
        "set")
    return perm_varnames, perms

def _process_dic(subtypes, subvals, idx, variables):
    """
    Returns an exhaustive list of possible values for the dict parameter 
    specified by the inputs. This dict can be nested arbitrarily deeply.
    """
    subtype, keywords = subtypes[idx]
    length_range = subvals[idx]
    varname, varrange, length_range = VAR_LOOKUP(length_range, variables)
    base_varname, possible_varnames = POSSIBLE_VARNAMES(varname, varrange, \
        length_range)

    ## Get the lists of all potential keys and values in this dictionary
    idx += 1
    key_subtypes, val_subtypes = subtypes[idx]
    key_subvals, val_subvals = subvals[idx]

    ## Get the processing functions for the keys and values
    first_key_subtype, first_key_keywords = key_subtypes[0]

    if first_key_subtype in PROCESS_FXNS:
        first_key_process_fxn = PROCESS_FXNS[first_key_subtype]
    else:
        first_key_process_fxn = PROCESS_FXNS[CLASS]

    first_val_subtype, first_val_keywords = val_subtypes[0]

    if first_val_subtype in PROCESS_FXNS:
        first_val_process_fxn = PROCESS_FXNS[first_val_subtype]
    else:
        first_val_process_fxn = PROCESS_FXNS[CLASS]

    ## For each of the keys and vals, dispatch to the appropriate 
    ## type-specific processing function
    nested_key_varnames, possible_keys = first_key_process_fxn(key_subtypes, \
        key_subvals, 0, variables)
    nested_val_varnames, possible_vals = first_val_process_fxn(val_subtypes, \
        val_subvals, 0, variables)

    ## Get all permutations of the possible keys and vals within the
    ## specified range of lengths 
    max_length = length_range[-1]
    min_length = length_range[0]
    perms, perm_varnames = _create_dict_perms(max_length, min_length, \
        base_varname, varrange, possible_keys, possible_vals, \
        nested_key_varnames, nested_val_varnames, keywords, varname)

    dict_perms = [(adict[0], (adict[1],)) for adict in perms]

    ## Convert perms from (keys_tuple, vals_tuple) to {key:val}
    return perm_varnames, dict_perms

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
### FINDING PERMUTATIONS:
###---------------------------------------------------
def _create_str_perms(max_length, min_length, domain):
    """
    Helper function for _process_str: 

    """
    if max_length == 0:
        ## Base case: the only zero-length option is the empty string
        return {"":True}

    else:
        ## Recursive case: find all valid strings of length l such that 
        ## min_length <= l <= max_length
        all_strs = {}

        ## Find all valid strings of length l such that 
        ## min_length <= l <= max_length - 1
        shorter_strs = _create_str_perms(max_length - 1, min_length, domain)

        ## Exhaustively append one character (from domain) to each option, and
        ## then include both the pre- and post-extended versions of the strings
        ## to all_strs
        for astr in shorter_strs:
            ## Add the string itself
            if astr not in all_strs and len(astr) >= min_length:
                all_strs[astr] = True

        for astr in shorter_strs:
            ## Add all extensions to the string
            for char in domain:
                if astr + char not in all_strs:
                    all_strs[astr + char] = True

        return all_strs

def _create_tup_perms(max_length, min_length, varname, varrange, next_vals, \
    nested_varnames, keywords, full_varname, typestr="tuple"):
    """
    Helper function for _process_tup (and _process_lst, and process_set): 
    finds and returns all permutations of the elements in next_vals such that 
    a) the result is valid according to the given keywords and b) the length 
    of the result is some l such that min_length <= l <= max_length.
    """
    ## First, get all permutations up to the max length
    perms, perm_varnames = _create_tup_perms_helper(max_length, min_length, \
        varname, varrange, next_vals, nested_varnames, keywords, \
        full_varname, typestr)

    final_perms = []
    final_varnames = []

    ## Second, filter out anything that's too short
    for i in range(len(perms)):
        if len(perms[i][1]) >= min_length:
            final_perms.append(perms[i])
            final_varnames.append(perm_varnames[i])

    return final_perms, final_varnames

def _create_tup_perms_helper(max_length, min_length, varname, varrange, \
    next_vals, nested_varnames, keywords, full_varname, typestr):
    """
    Helper function for _create_tup_perms: finds and returns all permutations 
    of the elements in next_vals such that a) the result is valid according 
    to the given keywords and varnames b) the length of the result is some l 
    such that l <= max_length.
    """
    if max_length == 0:

        ## Base case: the only zero-length option is an empty tuple
        if varrange:
            keys = [(typestr, (), ((varname, length),)) for length in varrange]
        else:
            keys = [(typestr, (), ((None, 0),))]

    else:
        ## Recursive case: find all valid tuples of length l such that 
        ## min_length <= l <= max_length
        all_tups = {}

        ## Find all valid tuples of length l such that 
        ## min_length <= l <= max_length - 1
        shorter_tups, dummy = _create_tup_perms_helper(max_length - 1, \
            min_length, varname, varrange, next_vals, nested_varnames, \
            keywords, full_varname, typestr)

        ## Exhaustively append one element (from next_vals) to each option, 
        ## and then include both the pre- and post-extended versions of the 
        ## tuples to all_tups
        for tup in shorter_tups:

            ## Add the tuple itself
            if tup not in all_tups and len(tup[1]) >= min_length:
                all_tups[tup] = True

            tup_varnames = tup[2]

            ## Add all expansions of this tuple
            for i in range(len(next_vals)):

                ## Expand the tuple by elem...
                elem = next_vals[i]
                elem_varnames = nested_varnames[i]

                ## ...but only if this elem's variable's value is consistent 
                ## with all other elements already in the tuple...
                if type(elem_varnames) == type([]):

                    ## Range: check all possible values; at most one can be 
                    ## valid
                    for elem_varname_opt in elem_varnames:
                        useme, combined_varnames = check_against_others( \
                            tup_varnames, elem_varname_opt)

                        if useme:
                            ## Construct a new tuple that results from adding elem to tup
                            expanded_tup = tup[1] + tuple([elem])
                            potential_key = (tup[0], expanded_tup, combined_varnames)

                            ## ...and also only if it's unique...
                            if potential_key not in all_tups:

                                ## ...and sorted, if requested!
                                if (typestr != "set" and SORTED not in \
                                    keywords) or len(tup[1]) == 0 or \
                                    (SORTED in keywords and elem >= tup[1][-1]) or \
                                    (typestr == "set" and elem > tup[1][-1]):
                                    all_tups[potential_key] = True

                else:

                    ## Absolute variable value
                    useme, combined_varnames = check_against_others(\
                        tup_varnames, elem_varnames)

                    if not useme:
                        ## (name, val) mismatch
                        continue

                    ## Construct a new tuple that results from adding elem to tup
                    expanded_tup = tup[1] + tuple([elem])
                    potential_key = (tup[0], expanded_tup, combined_varnames)

                    ## ...and also only if it's unique...
                    if potential_key not in all_tups:

                        ## ...and sorted, if requested!
                        if (typestr != "set" and SORTED not in \
                            keywords) or len(tup[1]) == 0 or \
                            (SORTED in keywords and elem >= tup[1][-1]) or \
                            (typestr == "set" and elem > tup[1][-1]):
                            all_tups[potential_key] = True

        keys = all_tups.keys()

    ## Filter the tuples we created according to variable usage
    filtered_keys = []

    for tup in keys:
        ## Actual length of the created tuple
        length = len(tup[1])

        for var in tup[2]:
            ## val = claimed length of the created tuple
            name, val = var
            if name == varname:
                break

        ## Don't filter based on "None"; don't filter out things that are the 
        ## requested length; don't filter out things that are supposed to be 
        ## longer than the max_length we're at currently
        if not name or val > max_length or ((type(full_varname) == type("") \
            and val == length) or (full_varname[0] == "start" \
            and val <= length) or (val >= length)):
            filtered_keys.append(tup)

    tup_varnames = [tup[2] for tup in filtered_keys]
    return filtered_keys, tup_varnames

def _create_dict_perms(max_length, min_length, varname, varrange, \
    possible_keys, possible_vals, nested_key_varnames, nested_val_varnames, \
    keywords, full_varname):
    """
    Helper function for _process_dict: finds and returns all permutations of 
    (key, val) pairs composed from possible_keys and possible_vals such that 
    a) the result is valid according to the given keywords and varnames and 
    b) the length of the result is some l such that min_length <= l <= 
    max_length.
    """
    ## First, get all permutations up to the max length
    perms, perm_varnames = _create_dict_perms_helper(max_length, min_length, \
        varname, varrange, possible_keys, possible_vals, \
        nested_key_varnames, nested_val_varnames, keywords, full_varname)

    final_perms = []
    final_varnames = []

    ## Second, filter out anything that's too short
    for i in range(len(perms)):
        if len(perms[i][1][0]) >= min_length:
            final_perms.append(perms[i])
            final_varnames.append(perm_varnames[i])

    return final_perms, final_varnames

def _create_dict_perms_helper(max_length, min_length, varname, varrange, \
    possible_keys, possible_vals, nested_key_varnames, nested_val_varnames, \
    keywords, full_varname):
    """
    Helper function for _process_dict: finds and returns all permutations of 
    (key, val) pairs composed from possible_keys and possible_vals such that 
    a) the result is valid according to the given keywords and varnames and 
    b) the length of the result is some l such that l <= max_length.
    """
    if max_length == 0:

        ## Base case: the only zero-length option is an empty dictionary, 
        ## which we will represent as a pair of empty tuples to make it 
        ## hashable, so that we can construct these permutations relatively 
        ## quickly
        if varrange:
            keys = [("dict", ((), ()), ((varname, size),)) \
                for size in varrange]
        else:
            keys = [("dict", ((), ()), ((None, 0),))]

    else:
        ## Recursive case: find all valid dictionaries of length l such that 
        ## min_length <= l <= max_length
        all_dicts = {}

        ## Find all valid dictionaries of length l such that 
        ## min_length <= l <= max_length - 1
        shorter_dicts, dummy = _create_dict_perms_helper(max_length - 1, \
            min_length, varname, varrange, possible_keys, possible_vals, \
            nested_key_varnames, nested_val_varnames, keywords, full_varname)

        ## Exhaustively append one element (from next_vals) to each option, 
        ## and then include both the pre- and post-extended versions of the 
        ## tuples to all_tups
        for adict in shorter_dicts:

            ## Add the dict itself
            if adict not in all_dicts:
                all_dicts[adict] = True

            dict_varnames = adict[2]

            ## Add all extensions to the dict
            for i in range(len(possible_keys)):
                key_elem = possible_keys[i]
                key_varnames = nested_key_varnames[i]

                if type(key_varnames) == type([]):

                    ## Range: check all possible values; at most one can be 
                    ## valid
                    for key_varname_opt in key_varnames:

                        ## Compare key names to shorter dict names
                        useme, combined_varnames = check_against_others( \
                            dict_varnames, key_varname_opt)

                        if not useme:
                            ## (name, val) mismatch
                            continue

                        ## Valid key; try all possible vals to go with it
                        for j in range(len(possible_vals)):
                            val_elem = possible_vals[j]
                            val_varnames = nested_val_varnames[j]

                            if type(val_varnames) == type([]):

                                ## Range: check all possible values; at most
                                ## one can be valid
                                for val_varname_opt in val_varnames:
                                    ## Compare val names to shorter dict names
                                    ## AND to key names
                                    useme, combined_varnames = \
                                        check_against_others( \
                                        combined_varnames, val_varname_opt)
                                    if useme:
                                        add_to_dict(all_dicts, adict, key_elem, \
                                            val_elem, new_combined_varnames)

                            else:
                                ## Compare val names to shorter dict names 
                                ## AND key names
                                useme, new_combined_varnames = \
                                    check_against_others( \
                                    combined_varnames, val_varnames)
                                if useme:
                                    add_to_dict(all_dicts, adict, key_elem, \
                                        val_elem, new_combined_varnames)
                           

                else:

                    ## Absolute variable value for key
                    ## Compare key names to shorter dict names
                    useme, combined_varnames = check_against_others(\
                        dict_varnames, key_varnames)

                    if not useme:
                        ## (name, val) mismatch
                        continue

                    ## Valid key; try all possible vals to go with it
                    for j in range(len(possible_vals)):
                        val_elem = possible_vals[j]
                        val_varnames = nested_val_varnames[j]

                        if type(val_varnames) == type([]):

                            ## Range: check all possible values; at most one
                            ## can be valid
                            for val_varname_opt in val_varnames:
                                ## Compare val names to shorter dict names
                                ## AND to key names
                                useme, combined_varnames = \
                                    check_against_others( \
                                    combined_varnames, val_varname_opt)
                                if useme:
                                    add_to_dict(all_dicts, adict, key_elem, \
                                        val_elem, new_combined_varnames)

                        else:
                            ## Compare val names to shorter dict names 
                            ## AND key names
                            useme, new_combined_varnames = \
                                check_against_others( \
                                combined_varnames, val_varnames)
                            if useme:
                                add_to_dict(all_dicts, adict, key_elem, \
                                    val_elem, new_combined_varnames)

        keys = all_dicts.keys()

    ## Filter the dicts we created according to variable usage
    filtered_keys = []

    for adict in keys:
        ## Actual length of the created tuple
        length = len(adict[1][0])

        for var in adict[2]:
            ## val = claimed length of the created tuple
            name, val = var
            if name == varname:
                break

        ## Don't filter based on "None"; don't filter out things that are the 
        ## requested length; don't filter out things that are supposed to be 
        ## longer than the max_length we're at currently
        if not name or val > max_length or ((type(full_varname) == type("") \
            and val == length) or (full_varname[0] == "start" \
            and val <= length) or (val >= length)):
            filtered_keys.append(adict)

    dict_varnames = [adict[2] for adict in filtered_keys]
    return filtered_keys, dict_varnames

def add_to_dict(all_dicts, adict, key_elem, val_elem, combined_varnames):
    """
    Helper function for adding a single expanded permutation 
    (adict + (key_elem, val_elem)) to the set of all dict permutations.
    """
    ## Since order doesn't matter for dictionaries, maintain 
    ## the keys in sorted order; otherwise we'll end up with 
    ## duplicates. Also, use > rather than >= so as to enforce
    ## uniqueness of keys within a single dictionary.
    if len(adict[1][0]) == 0 or key_elem > adict[1][0][-1]:

        ## Construct the new dict that results from adding 
        ## (key_elem, val_elem) to adict
        expanded_dict = ((adict[1][0] + tuple([key_elem])), \
            (adict[1][1] + tuple([val_elem])))
        potential_key = ("dict", expanded_dict, \
            combined_varnames)

        if potential_key not in all_dicts:
            all_dicts[potential_key] = True

###---------------------------------------------------
### TOP-LEVEL PROCESSING:
###---------------------------------------------------
def generate_exhaustive_cases():
    """
    Exhaustively generate test cases.
    """
    ## Generate unfiltered set test cases
    exhaustive_cases = process_types(method_spec, \
        CONVERT_TYPES(method_spec.TYPES), \
        method_spec.EXHAUSTIVE_VALS, method_spec.VARS, PROCESS_FXNS)

    ## Filter the test cases using the validation function; in doing so,
    ## convert all of the tuples of fields to actual class objects
    final_test_cases = []
    final_converted_test_cases = []
    for test_case in exhaustive_cases:

        ## Instantiate any classes (leaving it to the last minute here so 
        ## that we still have a serializable version to write to file)
        class_converted_args = CONVERT_CLASSES(method_spec, test_case, 
            method_spec.TYPES)

        ## Perform validation; only add this test case if it passes
        if not method_spec.evalidation_fxn(class_converted_args):
            continue

        ## Regenerate the non-class version of the test case, in case our
        ## validation function mutated it
        test_case = UNCONVERT_CLASSES(method_spec, class_converted_args, 
            method_spec.TYPES)

        final_test_cases.append(test_case)
        final_converted_test_cases.append(class_converted_args)

    ## Print the results
    #for test_case in final_converted_test_cases:
    #    print test_case
    #print "num exhaustive:", len(final_test_cases)

    ## Return both formats: one for (optionally) writing, and the other
    ## to be passed to the next stage in the pipeline
    return final_test_cases, final_converted_test_cases

def gen_write_exhaustive_cases(outfile):
    """
    Exhaustively generate test cases and write the output to a file.
    """
    ## Generate test cases
    test_cases, converted_test_cases = generate_exhaustive_cases()

    ## Write test cases to file
    f = open(outfile, "w")
    f.write("EXHAUSTIVE_CASES = " + repr(test_cases) + "\n")
    f.close()

    ## Return the Python object version
    return converted_test_cases
