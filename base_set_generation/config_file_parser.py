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
import copy
import os
import re
import string
import sys
import __builtin__
from bsg_globals import *

## Valid headers for the config file
EVALIDATION_HEADER = "[exhaustive validation]"
RVALIDATION_HEADER = "[random validation]"
CONSTRUCTORS_HEADER = "[constructors]"
TYPES_HEADER = "[types]"
EVALS_HEADER = "[exhaustive domain]"
RVALS_HEADER = "[random domain]"
VARS_HEADER = "[variables]"
RANDOM_HEADER = "[num random]"

MANDATORY_HEADERS = [TYPES_HEADER, EVALS_HEADER, RVALS_HEADER, RANDOM_HEADER]
OPTIONAL_HEADERS = [EVALIDATION_HEADER, RVALIDATION_HEADER, 
    CONSTRUCTORS_HEADER, VARS_HEADER]

## Paths for input and output files
CWD = os.path.dirname(os.path.realpath(__file__))
OUTFILE = CWD + "/method_spec.py"

## Keywords for specifying domains, types, etc.
ANY = "any"
CLASS = "class"

def _find_sublines(header_to_idx, header_inds, header, lines):
    """
    Helper function to make parse_config_file more robust: given a mapping of
    headers to starting indices, a sorted list of header start indices, the
    header for which to find the sublines, and the complete list of lines,
    returns a sublist of lines containing only the lines within the specified 
    header's section.
    """
    start_idx = header_to_idx[header]
    header_inds_idx = header_inds.index(start_idx)

    if header_inds_idx == len(header_inds) - 1:
        sublines = lines[start_idx:]
    else:
        end_idx = header_inds[header_inds_idx + 1]
        sublines = lines[start_idx: end_idx - 1]

    return sublines

def parse_config_file(projno, funcno, ms_outpath, importdir=None):
    """
    Parse the config file, whose name was passed as a command line arg, 
    and constructs two lists:

    -- TYPES, a list of sub-lists where one sub-list corresponds to a single 
       parameter, and this parameter is represented as a series of tuples of 
       (type, keywords) pairs.

       The i+1-th element in a sub-list is the type (with any specifiable 
       restrictions, as per the keywords) nested within the i-th type. Note 
       that this does not allow for mixed types within a container.

       Dictionaries are followed not by a tuple, but by a list containing two 
       sub-lists, which are themseslves the nested lists resulting from 
       recursively parsing the types of the keys and values in the dictionary.

    -- VALS, a list of sub-lists where one sub-list corresponds to a single 
       parameter, and this parameter is represented as a series of iterables 
       such that the i-th iterable is the domain of the corresponding type in  
       TYPES. Note that this assumes that the values are laid out in the same 
       order as their corresponding types, and this results in dictionaries 
       being laid out equivalently to in TYPES.

    Creates a file method_spec.py which imports the solution to the function
    to be tested and includes the definitions of TYPES and VALS. This file will
    later be used to this tuple to the parser_output.py file, which will later
    be used to a) generate test cases and b) check results.
    """
    ## Read the complete contents of the config file
    config_filename = CWD + "/../projects/project" + str(projno) + "/func" \
        + str(funcno) + ".cfg"
    f = open(config_filename, "r")

    lines = filter(len, [line[:-1] for line in f.readlines()])
    f.close()

    ## Find the mandatory headers
    header_to_idx = {}
    for header in MANDATORY_HEADERS:
        idx = lines.index(header) + 1
        header_to_idx[header] = idx

    ## Attempt to find the optional headers
    for header in OPTIONAL_HEADERS:
        try:
            idx = lines.index(header) + 1
            header_to_idx[header] = idx
        except:
            pass

    header_inds = header_to_idx.values()
    header_inds.sort()

    ## Parse all found sections!

    ## Validation: if unspecified, accept anything
    if EVALIDATION_HEADER in header_to_idx:

        ## Find the series of lines within this section
        sublines = _find_sublines(header_to_idx, header_inds, \
            EVALIDATION_HEADER, lines)
        import_str0 = parse_validation(sublines, "evalidation_fxn")

        ## Even though it's now optional, still accept opting out via present 
        ## but no contents
        if not import_str0:
            import_str0 = "from validation.default import accept_all as " \
                + "evalidation_fxn\n"

    else:
        import_str0 = "from validation.default import accept_all as " \
            + "evalidation_fxn\n"

    if RVALIDATION_HEADER in header_to_idx:

        ## Find the series of lines withi this section
        sublines = _find_sublines(header_to_idx, header_inds, \
            RVALIDATION_HEADER, lines)
        import_str1 = parse_validation(sublines, "rvalidation_fxn")

        ## Even though it's now optional, still accept opting out via present 
        ## but no contents
        if not import_str1:
            import_str1 = "from validation.default import accept_all as " \
                + "rvalidation_fxn\n"

    else:
        import_str1 = "from validation.default import accept_all as " \
            + "rvalidation_fxn\n"

    ## The meat of it: types of the parameters for this function
    types_sublines =_find_sublines(header_to_idx, header_inds, \
        TYPES_HEADER, lines)
    types = parse_types(types_sublines)

    ## Constructors and values rely on variable information (but it's 
    ## optional!)
    if VARS_HEADER in header_to_idx:
        variables = parse_vars(_find_sublines(header_to_idx, header_inds, \
            VARS_HEADER, lines))
    else:
        variables = {}

    ## Constructors args for all classes that appeared in the types list
    ## (again, optional)
    if CONSTRUCTORS_HEADER in header_to_idx:
        import_str2, dummy, constructors = parse_constructors( \
            _find_sublines(header_to_idx, header_inds, CONSTRUCTORS_HEADER, \
            lines), variables, 0)
    else:
        import_str2 = ""
        constructors = {}

    ## The other half of the meat of it: value ranges of the parameters for 
    ## this function
    exhaustive_vals = parse_vals(_find_sublines(header_to_idx, header_inds, \
        EVALS_HEADER, lines), types_sublines, variables)
    randomized_vals = parse_vals(_find_sublines(header_to_idx, header_inds, \
        RVALS_HEADER, lines), types_sublines, variables)

    ## Number of random test cases to be generated
    random = _find_sublines(header_to_idx, header_inds, RANDOM_HEADER, \
        lines)[0]

    ## Write the results to method_spec.py and ms_proj<projno>_func<funcno>.py
    f1 = open(OUTFILE, "w+")
    f2 = open(ms_outpath, "w+")
    f1.write("import sys\n\nsys.path.append(\"../projects/project" \
        + str(projno) + "/\")\n")
    f2.write("import sys\n\nsys.path.append(\"../../projects/project" \
        + str(projno) + "/\")\n")
    if importdir:
        f1.write("sys.path.append(\"../" + importdir + "\")\n")
        f2.write("sys.path.append(\"../../" + importdir + "\")\n")
    f1.write(import_str0)
    f1.write(import_str1)

    for outf in [f1, f2]:
        outf.write(import_str2 + "\n")
        outf.write("TYPES = " + str(types) + "\n")
        outf.write("EXHAUSTIVE_VALS = " + str(exhaustive_vals) + "\n")
        outf.write("RANDOMIZED_VALS = " + str(randomized_vals) + "\n")
        outf.write("VARS = " + str(variables) + "\n")
        outf.write("CONSTRUCTORS = " + str(constructors) + "\n")
        outf.write("RANDOMIZED_BOUND = " + random + "\n")
        outf.close()

def parse_validation(lines, as_what=None):
    """
    Parse the [validation] (and/or [solution], formerly) section of 
    the config file. Returns a string importing the required function(s) 
    and/or class(es) from the appropriate file(s).
    """
    retval = ""
    for line in lines:

        ## Skip blank lines
        if not line:
            continue

        ## Lines will be of the format "filename, fxn_name"
        filename, fxn_name = tuple([elem.strip() for elem in line.split(",")])
        filename = ".".join(filename.split(".")[0:-1])
        retval += "from validation." + filename + " import " + fxn_name
        if as_what:
            retval += " as " + as_what + "\n"
        else:
            retval += "\n"

    return retval

def parse_constructors(lines, variables, indentation=0, as_what=None):
    """
    Parse the [constructors] section of the config file. Returns a string 
    importing the required class(es) from the appropriate file(s), as well as
    a dictionary mapping class names to lists of arg types.
    """
    retval = ""
    constructors = {}
    init_vals = []

    for i in range(len(lines)):
        line = lines[i]

        ## Skip blank lines
        if not line:
            continue

        ## Break if we leave this level of indentation
        if string.find(line, "    " * indentation) != 0:
            return types

        ## Recurse on classes
        elif line.find(".py, ") > 0:
            class_name = line.split()[-1]

            ## The first line will be of the form "filename, class_name", 
            ## followed by a series of indented lines specifying the types of the 
            ## args to the constructor for the specified class
            filename, class_name = tuple([elem.strip() \
                for elem in line.split(",")])

            filename = ".".join(filename.split(".")[0:-1])
            retval += "from " + filename + " import " + class_name
            if as_what:
                retval += " as " + as_what + "\n"
            else:
                retval += "\n"

            importstr, fields, nested_constructors = parse_constructors(lines[i+1:], \
                variables, indentation + 1)

            ## Aggregate the nested information with the current-level 
            ## information
            retval += importstr
            constructors.update(nested_constructors)
            constructors[class_name] = fields

        ## Cleanup post class processing
        elif string.find(line, "    " * (indentation + 1)) == 0:
            continue

        else:
            init_vals.append(ast.literal_eval(line.strip()))

    return retval, init_vals, constructors

def parse_types(lines, indentation=0, class_name=None, \
    nested_class_fields=None):
    """
    Parse the [types] section of the config file. Returns types, a list of 
    sub-lists where one sub-list corresponds to a single parameter, and this
    parameter is represented as a series of tuples of (type, keywords) pairs.

    The i+1-th element in a sub-list is the type (with any specifiable 
    restrictions, as per the keywords) nested within the i-th type. Note that 
    this does not allow for mixed types within a container.

    Dictionaries are followed not by a tuple, but by a list containing two 
    sub-lists, which are themseslves the nested lists resulting from 
    recursively parsing the types of the keys and values in the dictionary.

    e.g. #1:
    dict (str: int) -> [('dict', ()), [[('str', ())], [('int'), ()]]]

    e.g. #2: 
    list (dict (tuple(str): dict (int: int))) ->
    [('list', ()), ('dict', ()), \
        [[('tuple', ()), ('str', ())], \
        [('dict', ()), [[('int', ()),], [('int', ())]]]]
    ]
    """
    ## Final list of types to be returned
    types = []
    in_class = False

    ## Process one arg at a time
    field_name = ""

    i = 0
    while i < len(lines):
        arg_type = lines[i]

        new_nested_class_fields = None
        new_class_name = None

        ## Skip blank lines
        if not arg_type:
            i += 1
            continue

        ## Break if we leave this level of indentation
        if string.find(arg_type, "    " * indentation) != 0:
            break

        ## Recurse on classes
        elif not class_name and CLASS in arg_type:
            new_nested_class_fields = parse_types(lines[i+1:], \
                indentation + 1)
            new_class_name = arg_type.split(CLASS)[-1].strip()

            for j in range(i+1, len(lines)):
                if string.find(lines[j], "    " * (indentation + 1)) != 0:
                    break

            if lines[j].strip()[0] == ":" or lines[j].strip()[0] == ")":
                arg_type = arg_type + lines[j]
                i = j
            else:
                i = j - 1

        ## Cleanup post class processing
        elif string.find(arg_type, "    " * (indentation + 1)) == 0:
            i += 1
            continue

        ## Keep track of the name, if we're dealing with a field 
        elif indentation > 0:
            field_name = arg_type.strip().split()[0]
            arg_type = " ".join(arg_type.strip().split()[1:])

        ## Parse this line
        nested_types = _parse_type(arg_type, new_class_name, \
            new_nested_class_fields)
        nested_types = _update_class(nested_types, new_class_name, \
            new_nested_class_fields)

        ## Add the list representation of the current line to the retval
        if field_name:
            types.append((field_name, [nested_types]))
        else:
            types.append(nested_types)

        i += 1

    return types

def _update_class(nested_types, new_class_name, new_nested_class_fields):
    """
    Helper function for inserting the field types in place of the class'
    generic placeholder.
    """
    if new_class_name:
        for k in range(len(nested_types)):

            if type(nested_types[k]) == type([]):
                ## Recursive case: dictionary!
                keys, vals = nested_types[k]
                updated_keys = _update_class(keys, new_class_name, new_nested_class_fields)
                updated_vals = _update_class(vals, new_class_name, new_nested_class_fields)

                nested_types[k] = [updated_keys, updated_vals]

            else:
                ## Base case: any other type!
                atype, keywords = nested_types[k]
                if CLASS in keywords:
                    nested_types[k] = (new_class_name, new_nested_class_fields)

                elif len(keywords) > 1 or (keywords and \
                    (not class_name and keywords[0] not in KEYWORDS[atype])):
                    raise ValueError

    return nested_types

def _parse_type(arg_type, class_name=None, nested_class_fields=None):
    """
    Parse a single nested type, returning it in the form of a list of 
    sub-lists where the i-th sub-list is the type of the i-th layer of 
    nesting.
    """
    nested_types = []

    ## Check for the presence of dictionaries
    nested_elems = arg_type.split(":")

    if len(nested_elems) == 1:

        ## Base case: no dictionaries :)
        ## Split this parameter into its layers of nesting
        nested_elems = re.split("[()]+", arg_type)
        nested_elems = filter(len, [elem.strip() for elem in nested_elems])
        final_nested_elems = []

        ## Process one layer of nesting at a time
        for elem in nested_elems:

            ## Separate the type itself from any keyword descriptors
            nested_subelems = elem.split()
            elem_type = nested_subelems[-1]

            ## Check that the type is valid
            if not class_name:
                try:
                    type_fxn = getattr(__builtin__, elem_type)
                except:
                    raise ValueError

            if len(nested_subelems) > 1:
                keywords = nested_subelems[:-1]
            else:
                keywords = []

            ## Check that the keywords are valid
            if keywords and (len(keywords) > 1 or \
                (not class_name and keywords[0] not in KEYWORDS[elem_type] \
                and not (elem_type == "str" and keywords[0][0] == "\"" and \
                keywords[0][-1] == "\""))):
                raise ValueError

            ## Build the list (nested_types) corresponding to this line, 
            ## which will be a sublist within the resultant types list
            nested_types.append((elem_type, tuple(keywords)))
    else:

        ## Recursive case: dictionaries :(
        ## We only need to worry about the very first occurrence of a 
        ## dictionary, as recursion will take care of any nested ones.

        ## Extract the "first half" (string describing the types of the 
        ## keys) and "second half" (string describing the types of the 
        ## values), to be recursed on
        nested_elems = arg_type.split(":")
        nested_elems = [elem.strip() for elem in nested_elems]
        first_half = nested_elems[0]
        second_half = ":".join(nested_elems[1:])

        first_half_num_open = first_half.count("(")
        first_half_num_closed = first_half.count(")")
        first_half_split = first_half.split("(")[(first_half_num_closed - first_half_num_open):]
        first_half_split = [elem.strip() for elem in first_half_split]
        first_half = "(".join(first_half_split).strip()
        pre_dict_num_open = first_half_num_open - first_half_num_closed
        second_half = second_half[:-1 * pre_dict_num_open]

        ## Recursively parse the keys and values as if they were stand-
        ## alone lines in the config file (thus being wrapped in lists)

        ## This assumes that there will only be a class in either the key OR
        ## the value, not both, which I think is perfectly safe since I can't
        ## imagine classes are hashable...
        first_half_parsed = parse_types([first_half], 0, class_name, \
            nested_class_fields)[0]
        second_half_parsed = parse_types([second_half], 0, class_name, \
            nested_class_fields)[0]

        ## Now, prepare to process everything up to the first dictionary
        nested_elems = re.split("[()]+", arg_type)
        nested_elems = filter(len, [elem.strip() for elem in nested_elems])
        final_nested_elems = []

        ## This need only be set false once, since we'll stop on hitting
        ## the first dictionary in the loop
        is_dict = False

        ## Process one layer of nesting at a time
        for i in range(len(nested_elems)):

            elem = nested_elems[i]
            if i == pre_dict_num_open - 1:
                is_dict = True

            ## Separate the type itself from any keyword descriptors
            nested_subelems = elem.split()
            elem_type = nested_subelems[-1]
              
            ## Check that the type is valid
            if not class_name:
                try:
                    type_fxn = getattr(__builtin__, elem_type)
                except:
                     raise ValueError

            if len(nested_subelems) > 1:
                keywords = nested_subelems[:-1]
            else:
                keywords = []

            ## Build the list (nested_types) corresponding to this line, 
            ## which will be a sublist within the resultant types list
            nested_types.append((elem_type, tuple(keywords)))

            ## When we reach the dictionary, append its [keys, values]
            ## list and then stop, as all else was parsed recursively
            if is_dict:
                nested_types.append([first_half_parsed, \
                    second_half_parsed])
                break

    return nested_types

def parse_vals(lines, type_lines, variables, indentation=0, class_name=None, \
    nested_class_fields=None):
    """
    Parse the [values] section of the config file, with some assistance from
    the [types] section. Returns values, a list of sub-lists where one 
    sub-list corresponds to a single parameter, and this parameter is 
    represented as a series of iterables such that the i-th iterable is the
    domain of the corresponding type from type_lines.
    """
    ## Final list of values to be returned
    values = []
    field_name = ""

    ## Process one arg at a time
    i = 0
    while i < len(lines):
        arg_val_line = lines[i]
        arg_type = type_lines[i]

        new_nested_class_fields = None
        new_class_name = None

        if not arg_val_line:
            i += 1
            continue

        ## Break if we leave this level of indentation
        if string.find(arg_val_line, "    " * indentation) != 0:
            break

        ## Recurse on classes
        elif CLASS in arg_val_line:
            new_class_name = arg_type.split(CLASS)[1].split()[0].strip()

            if not class_name:

                for j in range(i+1, len(lines)):
                    if string.find(lines[j], "    " * (indentation + 1)) != 0:
                        break

                if lines[j].strip()[0] == ":" or lines[j].strip()[0] == ")":
                    arg_val_line = arg_val_line + lines[j]
                    arg_type = arg_type + type_lines[j]
                    k = j
                else:
                    k = j - 1

                new_nested_class_fields = parse_vals(lines[i+1:], \
                    type_lines[i+1:], variables, indentation + 1)
                i = k

            else:
                new_nested_class_fields = nested_class_fields

        ## Cleanup post class processing
        elif string.find(arg_val_line, "    " * (indentation + 1)) == 0:
            i += 1
            continue

        ## Keep track of the name, if we're dealing with a field 
        elif indentation > 0:
            field_name = arg_val_line.strip().split()[0]
            arg_val_line = " ".join(arg_val_line.strip().split()[1:])

        ## Parse this line
        nested_values = _parse_val(arg_val_line, arg_type, variables, \
            new_class_name, new_nested_class_fields)

        if new_class_name:
            for k in range(len(nested_values)):
                val = nested_values[k]
                if CLASS in val:
                    nested_values[k] = (new_class_name, new_nested_class_fields)

        ## Add this parameter to the list
        if field_name:
            values.append((field_name, [nested_values]))
        else:
            values.append(nested_values)

        i += 1

    return values

def _parse_val(arg_val, arg_type, variables, class_name=None, \
    nested_class_fields=None):
    """
    Parse a single nested value, returning it in the form of a list of 
    sequences where the i-th sequence is the range of values for the i-th 
    layer of nesting.
    """
    ## Check for the presence of dictionaries
    nested_values = []
    nested_elems = arg_val.split(":")

    if len(nested_elems) == 1:
        ## Base case: no dictionaries :)

        ## Split this parameter into its layers of of nesting. We'll need
        ## both the values and the types, since the meaning of "any" 
        ## varies by type
        nested_elems = re.split("[()]+", arg_val)
        nested_elems = filter(len, [elem.strip() for elem in nested_elems])
        nested_type_elems = re.split("[()]+", arg_type)
        nested_type_elems = filter(len, [elem.strip() for elem in \
            nested_type_elems])

        ## Process one layer of nesting at a time
        for i in range(len(nested_elems)):
            elem = nested_elems[i]
            type_elem = nested_type_elems[i]

            if elem == ANY:
                ## The domain is unrestricted
                if "bool" in type_elem:
                    nested_values.append([True, False])

                elif "list" in type_elem:
                    nested_values.append(xrange(0, sys.maxint / 2))

                else:
                    nested_values.append(xrange(-1 * sys.maxint / 2, \
                        sys.maxint / 2))

            elif elem[0] == "[":
                ## The domain is specified as an absolute list
                nested_values.append(ast.literal_eval(elem))

            elif "-" in elem:
                ## The domain is specified as a range "start-end"
                start, end = tuple([range_end.strip() \
                    for range_end in elem.split("-")])

                if start == ANY:
                    start = -1 * sys.maxint
                if end == ANY:
                    end = sys.maxint - 1

                ## If a variable is used in the range, just store the 
                ## whole string for now
                try:
                    start = int(start)
                except:
                    if start not in variables:
                        raise ValueError
                    nested_values.append(elem)
                    continue

                try:
                    end = int(end)
                except:
                    if end not in variables:
                        raise ValueError
                    nested_values.append(elem)
                    continue

                ## Otherwise create an appropriate xrange object
                nested_values.append(xrange(start, end + 1))

            else:
                ## The domain is a variable name; make sure we have a
                ## definition for it first
                if elem not in variables and CLASS not in elem:
                    raise ValueError

                nested_values.append(elem)

    else:

        ## Recursive case: dictionaries :(
        ## We only need to worry about the very first occurrence of a 
        ## dictionary, as recursion will take care of any nested ones.

        ## Extract the "first half" (string describing the types of the 
        ## keys) and "second half" (string describing the types of the 
        ## values), to be recursed on
        nested_elems = arg_val.split(":")
        nested_elems = [elem.strip() for elem in nested_elems]
        first_half = nested_elems[0]
        second_half = ":".join(nested_elems[1:])

        nested_type_elems = arg_type.split(":")
        nested_type_elems = [elem.strip() for elem in nested_type_elems]
        first_type_half = nested_type_elems[0]
        second_type_half = ":".join(nested_type_elems[1:])

        first_half_num_open = first_half.count("(")
        first_val_half_split = first_half.split("(")
        first_half = "(".join(first_val_half_split[1:])
        second_half = second_half[:-1]#first_half_num_open]

        ## Recursion will demand stand-alone representations of the types
        ## as well as the values
        first_type_half_split = first_type_half.split("dict")
        first_type_half_split = [elem.strip() \
            for elem in first_type_half_split]   
        first_type_half = first_type_half_split[1][1:]
        second_type_half = second_type_half[:-1]

        ## Recursively parse the keys and values as if they were stand-
        ## alone lines in the config file (thus being wrapped in lists)
        first_half_parsed = parse_vals([first_half], [first_type_half], \
            variables, 0, class_name, nested_class_fields)[0]
        second_half_parsed = parse_vals([second_half], \
            [second_type_half], variables, 0, class_name, \
            nested_class_fields)[0]

        ## Split both the types and values of this parameter into its 
        ## layers of of nesting
        nested_elems = re.split("[()]+", arg_val)
        nested_elems = filter(len, [elem.strip() for elem in nested_elems])
        nested_type_elems = re.split("[()]+", arg_type)
        nested_type_elems = filter(len, [elem.strip() \
            for elem in nested_type_elems])

        ## This need only be set false once, since we'll stop on hitting
        ## the first dictionary in the loop
        is_dict = False

        ## Process one layer of nesting at a time
        for i in range(len(nested_elems)):

            ## We need the type to be able to check if we've reached the
            ## (first) dictionary; after that we'll ignore it
            elem = nested_elems[i]
            type_elem = nested_type_elems[i]
            if "dict" in type_elem:
                is_dict = True

            if elem == ANY:
                ## The domain is unrestricted
                nested_values.append(xrange(-1 * sys.maxint / 2, \
                    sys.maxint / 2))

            elif elem[0] == "[":
                ## The domain is specified as an absolute list
                nested_values.append(ast.literal_eval(elem))

            elif "-" in elem:
                ## The domain is specified as a range "start-end"
                start, end = tuple([range_end.strip() \
                    for range_end in elem.split("-")])

                if start == ANY:
                    start = -1 * sys.maxint
                if end == ANY:
                    end = sys.maxint - 1

                nested_values.append(xrange(int(start), int(end) + 1))

            else:
                ## The domain is a variable
                nested_values.append(elem)

            ## When we reach the dictionary, append its [keys, values]
            ## list and then stop, as all else was parsed recursively
            if is_dict:
                nested_values.append([first_half_parsed, \
                    second_half_parsed])
                break

    return nested_values

def parse_vars(lines):
    """
    Parse the [variables] section of the config file. Returns a mapping of each
    variable name to its valid range of values.
    """
    variables = {}

    for line in lines:

        ## Skip blank lines
        if not line:
            continue

        ## Variable's range will be defined in the form "varname start-end";
        ## add it to the mapping in the form {varname: xrange(start, end + 1)}
        fields = line.split()
        varname = fields[0]
        start, end = tuple([int(x) for x in [range_end.strip() for range_end in \
            fields[1].split("-")]])
        variables[varname] = xrange(start, end + 1)

    return variables

def parse_split(lines):
    """
    Parse the [percent exhaustive] section of the config file. Returns a tuple
    of (percent exhaustive), (percent randomized). That adds up to 100.
    """
    for line in lines:

        ## Skip blank lines
        if not line:
            continue

        exhaustive = int(line.strip())
        randomized = (100 - exhaustive)
        exhaustive = exhaustive * 0.01
        randomized = randomized * 0.01

        return (exhaustive, randomized)


if __name__ == "__main__":
    ## Expect one arg, the name of the file to be parsed, and do said parsing!
    parse_config_file(CWD + "/" + sys.argv[1])
