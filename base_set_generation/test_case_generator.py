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

import ast
import inspect
import math
import random
import string
import sys
import __builtin__

from bsg_globals import *

###---------------------------------------------------
### MACROS: 
###---------------------------------------------------
def CONVERT_TYPES(types):
    """
    Converts a types list of the form output by configFileParser.py (to
    method_spec.py) into an equivalent list with type objects replacing type
    names (originally strings). 
    """
    ## Process one parameter at a time
    new_types = []
    for subtypes in types:

        ## Process one layer of nesting at a time
        new_subtypes = []
        for subtype in subtypes:

            if type(subtype) == type(()):
                ## Base case: convert the first element of the tuple into the
                ## appropriate type object
                try:
                    new_subtypes.append((getattr(__builtin__, subtype[0]), \
                        subtype[1]))
                except:
                    ## Class!
                    name = subtype[0]
                    field_subtypes = subtype[1]

                    new_field_subtypes = []
                    for field_name, field_subtype in field_subtypes:
                        conversion = CONVERT_TYPES(field_subtype)
                        new_field_subtypes.append((field_name, conversion))

                    new_subtypes.append((name, new_field_subtypes))

            else: 
                ## Recursive case: type(subtype) == type([]) (dictionary keys
                ## and values)
                new_subtypes.append(CONVERT_TYPES(subtype))

        new_types.append(new_subtypes)

    return new_types

def VAR_LOOKUP(possible_vals, variables):
    """
    Looks up the given variable in the dictionary of variables and transform s
    it as necessary; returns the variable's name and the resultant possible 
    values.
    """
    varname = None
    varrange = None

    if type(possible_vals) == type(""):

        if "-" in possible_vals:

            ## Special case: one of the endpoints of a range is a variable.
            ## Note that both being variables is disallowed.
            start, end = tuple([range_end.strip() for range_end in \
                possible_vals.split("-")])

            try:
                varname = (END, end)
                start = int(start)
                end = variables[end]
                possible_vals = xrange(start, end[-1] + 1)
                varrange = end

            except:
                varname = (START, start)
                start = variables[start]
                end = int(end) + 1
                possible_vals = xrange(start[0], end)
                varrange = start

        else:
            ## Easy case: the entire value is a variable
            varname = possible_vals
            possible_vals = variables[possible_vals]
            varrange = possible_vals

    return varname, varrange, possible_vals

def IS_RANGE(varname):
    """
    Returns true if the input varname is part of a range; false otherwise.
    """
    return type(varname) == type(()) and (varname[0] == START \
        or varname[0] == END)

def CONVERT_CONTAINER(method_spec, container, nested_expected_types):
    """
    Helper function for converting nested tuples of the form:
    (typestr, (typestr, (typestr, obj))) into nested objects of the intended 
    types (as identified by the typestrs).
    """
    if len(container) == 0:
        return container

    ## Create an empty container of the appropriate type
    first = container[0]
    type_fxn = getattr(__builtin__, first)
    retval = type_fxn()

    ## Recursively process everything in this container
    rest = container[1]

    if type_fxn == dict:

        ## Get the types of the keys and values
        key_type = nested_expected_types[0][0]
        val_type = nested_expected_types[0][1]

        ## Get the actual keys and values
        keys = rest[0][0]
        vals = rest[0][1]
        pairs = zip(keys, vals)

        for key, val in pairs:
            ## Convert each (key, val) pair...
            converted_key = CHECK_CONVERT(method_spec, key, key_type)
            converted_val = CHECK_CONVERT(method_spec, val, val_type)

            ## ...and add it to the dictionary
            retval = APPEND(retval, (converted_key, converted_val))

    else:

        ## Convert each element and add it to the container
        for elem in rest:
            retval = APPEND(retval, CHECK_CONVERT(method_spec, elem, \
                nested_expected_types, CONVERT_CONTAINER))

    return retval

def CHECK_CONVERT(method_spec, container, expected_types, 
    conversion_fxn=CONVERT_CONTAINER):
    """
    Helper function which optionally (if they are containers or classes) 
    converts the input containers using the specified conversion function.
    """
    if type(container) != type(()):
        return container

    elif container[0] in CONTAINER_TYPES:

        ## We stored all (nested) lists, sets, and tuples as tuples 
        ## during generation, so that we could hash them to perform quick 
        ## checks for duplicates; but, now we want to convert them back 
        ## to their intended types
        container = conversion_fxn(method_spec, container, expected_types[1:])

    elif expected_types[0][0] in method_spec.CONSTRUCTORS:

        ## Convert each individual field, aggregating the results
        retval = []
        for i in range(len(container)):
            field = container[i]
            retval.append(CHECK_CONVERT(method_spec, field, \
                expected_types[0][1][i][1][0]))

        container = tuple(retval)

    else:
        ## Unidentified type
        raise ValueError

    return container

def APPEND(container, elem):
    """
    Appends the element to the given container (which could be a list, set, or
    tuple).
    """
    if type(container) == type([]):
        container.append(elem)

    elif type(container) == type(set([])):
        container.add(elem)

    elif type(container) == type(()):
        container = container + (elem,)

    elif type(container) == type({}):
        container[elem[0]] = elem[1]

    return container

def POSSIBLE_VARNAMES(varname, varrange, possible_args, f=(lambda x: x)):
    """
    Given the name and range of a variable, as well as the range of possible 
    arguments, creates a tuple of sub-tuples of (varname, val) pairs, where 
    the i-th sub-tuple corresponds to all of the values of varname that are 
    compatible with the i-th element in possible_args.
    """
    ## Case 1: absolute value
    if type(varname) != type(()):
        possible_varnames = [tuple([(varname, f(arg))]) for arg in \
            possible_args]
        base_varname = varname

    ## Case 2: start of a range
    elif varname[0] == START:
        possible_varnames = [[((varname[1], val),) for val in \
            filter(lambda x: x <= f(arg), varrange)] for arg in possible_args]
        base_varname = varname[1]

    ## Case 3: end of a range
    else:
        possible_varnames = [[((varname[1], val),) for val in \
            filter(lambda x: x >= f(arg), varrange)] for arg in possible_args]
        base_varname = varname[1]

    return base_varname, possible_varnames

def CONVERT_CLASSES(method_spec, arg_list, types):
    """
    Given a list of args in the form of nested tuples, converts all classes
    into objects of the appropriate type.
    """
    new_arg_list = []

    for i in range(len(types)):
        arg_type = types[i]
        arg_val = arg_list[i]

        if arg_type[0][0] in CONTAINER_TYPES:

            ## Recursive case #1: container, which might contain classes
            ## Make an empty container of the appropriate type 
            type_fxn = getattr(__builtin__, arg_type[0][0])
            container = type_fxn()

            rest = arg_type[1:]

            if type_fxn == dict:

                key_type = arg_type[1][0]
                val_type = arg_type[1][1]

                ## Process each (key, val) pair in the original dict, and 
                ## add it to our new (actual) dict
                for key, val in arg_val.items():
                    converted_key = CONVERT_CLASSES(method_spec, [key], 
                        [key_type])[0]
                    converted_val = CONVERT_CLASSES(method_spec, [val], 
                        [val_type])[0]
                    container = APPEND(container, (converted_key, \
                        converted_val))

            else:

                ## Process each element in the original container, and add
                ## it to our new container
                elem_type = arg_type[1:]
                for elem in arg_val: 
                    converted_elem = CONVERT_CLASSES(method_spec, [elem], 
                        [elem_type])
                    container = APPEND(container, converted_elem[0])

            ## Add this new container to the list
            new_arg_list.append(container)
            continue

        elif arg_type[0][0] not in method_spec.CONSTRUCTORS:
            ## Base case: not a class; nothing to be done!
            new_arg_list.append(arg_val)
            continue

        ## Recursive case #2: class!
        arg_type = arg_type[0]
        class_name = arg_type[0]
        fields = arg_type[1]

        ## Get the constructor for this class
        constructor = getattr(method_spec, class_name)
        constructor_args = method_spec.CONSTRUCTORS[class_name]

        ## Instantiate the class object with these nonsense args for now
        class_instance = constructor(*constructor_args)

        ## Now, overwrite the fields with their true values
        for j in range(len(fields)):
            field_name = fields[j][0]
            field_val = arg_val[j]
            setattr(class_instance, field_name, field_val)

        ## Add this class instance to the arg list
        new_arg_list.append(class_instance)

    return tuple(new_arg_list)

def UNCONVERT_CLASSES(method_spec, arg_list, types):
    """
    Given a list of args in the form of objects, converts all class objects
    back into tuples of fields.
    """
    new_arg_list = []

    for i in range(len(types)):
        arg_type = types[i]
        arg_val = arg_list[i]

        if arg_type[0][0] in CONTAINER_TYPES:

            ## Recursive case #1: container, which might contain classes
            ## Make an empty container of the appropriate type 
            type_fxn = getattr(__builtin__, arg_type[0][0])
            container = type_fxn()

            rest = arg_type[1:]

            if type_fxn == dict:

                key_type = arg_type[1][0]
                val_type = arg_type[1][1]

                ## Process each (key, val) pair in the original dict, and 
                ## add it to our new (actual) dict
                for key, val in arg_val.items():
                    converted_key = UNCONVERT_CLASSES(method_spec, [key], 
                        [key_type])[0]
                    converted_val = UNCONVERT_CLASSES(method_spec, [val], 
                        [val_type])[0]
                    container = APPEND(container, (converted_key, \
                        converted_val))

            else:

                ## Process each element in the original container, and add
                ## it to our new container
                elem_type = arg_type[1:]
                for elem in arg_val: 
                    converted_elem = UNCONVERT_CLASSES(method_spec, [elem], 
                        [elem_type])
                    container = APPEND(container, converted_elem[0])

            ## Add this new container to the list
            new_arg_list.append(container)
            continue

        elif arg_type[0][0] not in method_spec.CONSTRUCTORS:
            ## Base case: not a class; nothing to be done!
            new_arg_list.append(arg_val)
            continue

        ## Recursive case #2: class!
        arg_type = arg_type[0]
        class_name = arg_type[0]
        fields = arg_type[1]
        class_instance = arg_val

        ## Now, overwrite the fields with their true values
        new_fields = []
        for j in range(len(fields)):
            field_name = fields[j][0]
            field_val = getattr(class_instance, field_name)
            ## NOTE: not currently set up to support nested classes
            new_fields.append(field_val)

        ## Add this class instance to the arg list
        new_arg_list.append(tuple(new_fields))

    return tuple(new_arg_list)

###---------------------------------------------------
### POST-PROCESSING OF VARIABLE DEPENDENCIES:
###---------------------------------------------------
def check_against_others(my_varnames, existing_varnames):
    """
    Checks for consistency of variable name usage across args, where 
    my_varnames is the set of varnames belonging to the object that is a 
    candidate for addition to the arg list, and existing_varnames is the set 
    of varnames contributed by the other objects that are already part of the
    arg list. 

    Returns True or False for valid or invalid, as well as (in the valid case)
    an updated set of names contributed by all objects in the list (including 
    this).
    """
    new_varnames = []

    if type(my_varnames) == type([]):

        ## Primitive type whose value hasn't been fixed yet
        my_name = my_varnames[0][0]
        not_added = [list(my_varnames[:])]

        ## Matches are not necessary for None
        if my_name:

            ## Compare against all names that have been established thus far
            matched = False
            for existing_varname in existing_varnames:
                existing_name, existing_vals = existing_varname

                ## Check for discrepancies, if the names are the same
                if my_name == existing_name:
                    for my_possible_varname in my_varnames:
                        dummy, my_vals = my_possible_varname

                        if my_vals == existing_vals:
                            new_varnames.append(my_possible_varname)
                            not_added.remove(my_possible_varname)
                            matched = True
                            break

                    if not matched:
                        ## Incompatible values
                        return False, None

    else:

        ## Value is already fixed
        not_added = list(my_varnames[:])

        for my_varname in my_varnames:
            my_name, my_vals = my_varname

            ## Matches are not necessary for None
            if not my_name:
                continue

            ## Compare against all names that have been established thus far
            for existing_varname in existing_varnames:
                existing_name, existing_vals = existing_varname

                if not existing_name:
                    continue

                ## Check for discrepancies, if the names are the same
                if my_name == existing_name:

                    if my_vals != existing_vals:
                        ## Incompatible values
                        return False, None

                    new_varnames.append(my_varname)
                    not_added.remove(my_varname)

        new_varnames.extend(not_added)

    ## Add all names contributed by other args that are not also covered by 
    ## this arg's names
    new_names = [name[0] for name in new_varnames]
    for existing_varname in existing_varnames:
        existing_name, existing_vals = existing_varname
        if existing_name not in new_names:
            new_varnames.append(existing_varname)

    return True, tuple(new_varnames)

###---------------------------------------------------
### TOP-LEVEL PROCESSING:
###---------------------------------------------------
def process_types(method_spec, types, vals, variables, process_fxns):
    """
    Processes all of the parameters, exhaustively generating all possible
    args for each one. Then, creates all possible arg lists by combining
    the possible args across all of the parameters.
    """
    possible_args = process_types_rec(types, vals, variables, process_fxns)

    ## Recursively create all possible sets of parameters; in doing so,
    ## post-process the options to filter out combinations that don't satisfy
    ## variable usage
    arg_lists = []
    generate_arg_lists(possible_args, 0, arg_lists, variables)

    ## Filter out duplicates:
    arg_lists = set([arg_list[1] for arg_list in arg_lists])

    ## Convert all of the arg lists away from the hashable format
    converted_arg_lists = []
    for arg_list in arg_lists:

        ## Convert each individual arg in this list
        converted_arg_list = []
        for i in range(len(arg_list)):
            val = arg_list[i]
            converted_val = CHECK_CONVERT(method_spec, val, types[i])
            converted_arg_list.append(converted_val)

        converted_arg_lists.append(converted_arg_list)

    return converted_arg_lists

def process_types_rec(types, vals, variables, process_fxns):
    """
    Processes all of the parameters, exhaustively generating all possible 
    args for each one and returning this list (of lists) of possible args.
    """
    possible_args = []

    ## Process one parameter at a time
    for i in range(len(types)):
        nested_type = types[i]
        nested_val = vals[i]
        do_convert = False

        first_subtype, first_keywords = nested_type[0]

        ## Dispatch to the top-level type-specific processing function, which 
        ## will call all others as needed
        if first_subtype in process_fxns:
            ## Base case: primitive type!
            first_process_fxn = process_fxns[first_subtype]
            retval = first_process_fxn(nested_type, nested_val, 0, variables)

        else:
            ## Recursive case: class!
            first_process_fxn = process_fxns[CLASS]
            retval = first_process_fxn(nested_type, nested_val, 0, variables)

        ## Add all possible args for the i-th parameter
        possible_args.append(retval)

    return possible_args

def generate_arg_lists(possible_args, idx, arg_lists, variables):
    """
    Given possible_args, a list of sub-lists where the i-th sub-list contains 
    all possible  values for the i-th parameter, creates and returns a list of
    all possible "argument lists", where one argument list is actually a tuple 
    containing one possible value for each parameters.

    Note that this is the function that makes sure all of the variable 
    specifications are adhered to.

    e.g. possible_args = [[1, 2], ["a", "b"]]
         output = [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
    """
    new_arg_lists = []

    if idx == len(possible_args):
        ## Base case: no parameters left to be processed
        arg_lists.append(((), ()))
        return

    else:
        ## Recursive case: generate arg lists encapsulating parameters from 
        ## index idx + 1 onwards
        generate_arg_lists(possible_args, idx + 1, arg_lists, variables)
        all_varnames = [possible_args[i][0] for i in range(len(possible_args))]
        this_varnames = possible_args[idx][0]
        my_possible_args = possible_args[idx][1]

        ## Add all valid combos including all possible values of this 
        ## (idx-th) parameter 
        for i in range(len(possible_args[idx][1])):
            opt = possible_args[idx][1][i]
            opt_varnames = this_varnames[i]

            ## Look at all current combos for params (idx:end], and try
            ## prepending opt as the idx-th parameter's value
            for arg_list in arg_lists:
                existing_varnames = arg_list[0]
                args = arg_list[1]

                ## Check for variable usage consistency
                do_append, combined_varnames = check_against_others(opt_varnames, \
                    existing_varnames)

                if do_append:
                    if type(opt_varnames) == type([]) and \
                        (opt_varnames[0][0][0] not in [cv[0] for cv in \
                        combined_varnames]):
                        for opt_varname_opt in opt_varnames:
                            new_arg_lists.append((opt_varname_opt + \
                                combined_varnames, (opt,) + args))
                    else:
                        new_arg_lists.append((combined_varnames, (opt,) + args))

    del arg_lists[:]
    arg_lists.extend(new_arg_lists)
