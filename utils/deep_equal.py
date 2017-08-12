"""
Generalized deep equality tester for arbitrary data structures

ONLY WORKS FOR OLD STYLE CLASSES!   SEE OBJECT COMPARISON CODE
Copyright (c) 2014 Stephen Wong [swong@rice.edu]
"""

#### NEEDS LOOP DETECTION!  ####

import datetime, time, operator, types, collections, cgi, cmath
import logging, traceback

InexactNumberTypes = [types.FloatType,  types.ComplexType]
NumberTypes = [types.IntType, types.LongType] + InexactNumberTypes
DateTimeTypes = [datetime.date, datetime.datetime, datetime.time, datetime.timedelta, time.struct_time]

class _DummyClass:
    pass
InstanceType = type(_DummyClass())


DEEP_EQUALS_METHOD = "__deep_equals__"   # this_obj.__deep_equals__(other_obj, deep_equals_fn)

class DeepEqualsError(Exception):
    """
    Class that represents a structural error encountered during a deep equality test
    """
    
    def __init__(self, *args, **kwargs):
        super(DeepEqualsError, self).__init__(*args, **kwargs)
        
        
class _AlreadySeen:
    """
    Private class used for memo-izing already processed nodes in the data structure for use in loop detection.
    """
    
    def __init__(self):
        """
        Initialize the internal records
        """
        self.ref = {}
        self.test = {}
        
    def is_loop(self, ref_val, test_val):
        """
        Loop detection utility.  Returns True if an expected loop is detected, i.e. both ref_val and test_val are circular references
        and test_val is the same reference as was encountered with the previous ref_val.  Returns False if no loop was detected or expected.
        The function does NOT type check its inputs!   It uses the id(value) for reference comparison.
        Throws a DeepEqualsError (missing circular reference) if ref_val is a circular reference but test_val is not the same reference 
        as was previously encountered with the previous ref_val encounter.  Also throws a DeepEqualsError (unexpected circular reference) 
        if test_val is a circular reference but ref_val is not.  
        If no circular reference is detected then ref_val and test_val are added to the internal records for subsequent loop detections.
        """
        ref_id = id(ref_val)
        test_id = id(test_val)
        if ref_id in self.ref:   # ref structure has a loop here
            if test_id == self.ref[ref_id]["test_id"]:
                return True    # structurally correct loop detected.
            else:    # test structure is not looping when it should
                raise DeepEqualsError("(Exception: Missing Circular Reference)  A circular reference was expected here.  <br/>Expected <br/>{0} (ID = {1}) <br/>but received <br/>{2} (ID = {3})<br/>Note that the only visible difference may be the value's ID number.".format(self.ref[ref_id]["test_val"], self.ref[ref_id]["test_id"], test_val, test_id))
        elif test_id in self.test:
            raise DeepEqualsError("(Exception: Unexpected Circular Reference)  An invalid circular reference was detected.  <br/>Expected <br/>{0} but found <br/>{1}<br/>Note that difference may not be visible here.".format(self.test[test_id]["ref_val"], test_val))
        else:   # no loop, so add to internal records for later checking
            self.ref[ref_id] = {"test_id": test_id, "test_val":test_val}
            self.test[test_id] = {"ref_val":ref_val}
            return False    

def deep_equal(ref_val, test_val, strict_typing = True, time_tol = 1.0, float_tol = 1.0e-10):
    """
    Performs a deep equality check of a given test value relative to a given reference value.  
    Returns True if the structure, types and corresponding values are equal, subject to tolerance and 
    strict typing options.  Returns False if the structure and types match but the values are not equal,
    subject to strict typing options. 
    
    ref_val = the reference value being tested against.
    test_val = the value to test against ref_val
    
    Will recursively test down through arbitrary combinations of list, tuples, dictionaries, sets, 
    generators, iteratables, sequences, mappings, etc.   Can handle ints, floats, longs, strings, date/time and objects.
    
    RESTRICTIONS:  
    - Non-sequence, non-dictionary sub-components must have a definable length and be uniquely sortable.
    - Uses a recursive algorithm, so deeply nested structures run the risk of overflowing the stack.
    - For collection.defaultdict, the test dictionary must explicitly contain all the explicitly defined keys in the 
        reference dictionary.  Auto-generated key-values are not considered part of the dictionary.

    
    OPTIONS:
        float_tol = the floating point tolerance to use when comparing floats or complex numbers or any numbers when 
            strict_typing has 'num':False.  If float_tol > 0.0, then the tolerance is considered to be a relative size, 
            i.e. True is returned for float_tol >= abs((ref_val - test_val)/ref_val). 
            If float_tol < 0.0, the tolerance is considered to be an absolute difference, where True is returned for 
            abs(float_tol) >= abs(ref_val - test_val).   If ref_val == 0.0, then float_tol is always considered to be 
            an absolute difference.  float_tol defaults to 1.0E-10.
            
        time_tol = the absolute difference in seconds allowed to consider the reference and test times to be the same.
            time_tol defaults to 1.0 seconds.
            
        strict_typing = Determines whether strict typing of the value is used when considering equality.  By default, all compared
            entities must have exactly the same type or a TypeError exception will be thrown.  strict_typing can be specified 
            as a dictionary whose keys specify which types can be "loose" and thus be considered equal even though their types don't 
            exactly match.   The available strict typing keys are (all True by default):
            
            "map" : If False, allows any types.Mapping (dictionary) instance to be compared.   The keys must match exactly however.
            "map_keys" : If False, allows the reference mapping's keys to simply be a subset of the test mapping's keys.
            "iter" : If False, allows any types.Iterable to be compared though sequences cannot be 
                compared to non-sequences. 
            "bool" : If False, allows any value that behaves as a boolean to be compared against a reference bool value.
            "num" : If False, allows ints, longs and floats to be compared.  The float_tol will be used for any compares that involve different types. 
            "str" : If False, allows ASCII strings and Unicode strings to be compared and is case-insensitive.
            "obj" : If False, the reference object's __eq__() method is used to compare against the test object, 
                independent of the reference and test object's actual classes.
            
            Any strict_typing keys not specified in the given strict_typing dictionary will be set to True. 
            Any unrecognized keys will be ignored.
            
            For convenience, strict_typing = True (default) sets all the above typing options to True and 
            strict_typing = False sets them all to False. 
            
            
        EXCEPTIONS THROWN:
            TypeError - When incompatible types are being compared
            IndexError - When compared iterables have the mismatched lengths/sizes, including dictionary keys under strict typing. 
            
        For deep equality testing of objects, if either the reference or test object has a method "__deep_equals__(self, other_obj, deep_equal_fn)" 
        it will be called, with a preference for the method on the reference object.  The __deep_equals__ method does not have to do any loop
        checking, but it should do a check that the other object is a compatible object, e.g. is a subclass of the itself.   All __deep_equals__ then needs to
        do is to recurse into its attributes, calling deep_equal_fn(self.attribute, other.attribute) for each desired attribute, returning True if all recursions return True or 
        False if any one fails.  The deep_equal_fn will return True or False or throw a deep_equal.DeepEqualsError exception on structural errors.
        
        If neither object has a __deep_equals__ method, then a "ref_obj == test_obj" equality test will be performed, following the Python rules for
        invoking a __eq__ method if defined (preferentially on the reference object). 
    """
    
    ### Set up the strict vs. loose typing ########
    strict_typing_dict = { "map":True,  "map_keys": True, "iter": True, "bool":True, "num":True, "str": True, "obj":True}
    
    if isinstance(strict_typing, bool):
        if strict_typing == False:
            for key in strict_typing_dict:
                strict_typing_dict[key] = False
    elif isinstance(strict_typing, dict):
        strict_typing_dict.update(strict_typing)
    else: 
        raise TypeError("deep_equal.deep_equal() called with strict_typing = {0} which is neither a boolean nor a dictionary.".format(strict_typing))

    ###### Curry the recursive helper functions with the option parameters  ###########
    
    def _deep_dict_eq(ref_dict, test_dict, already_seen):
        """
        Equality test for dictionaries.
        Already established that ref_dict is type collections.Mapping
        """

        if (strict_typing_dict["map"] and type(ref_dict) != type(test_dict)):
            raise DeepEqualsError("(Exception: Invalid Types) Expected {0} type = {1} but received {2} type = {3}".format(type_str(ref_dict), ref_dict, type_str(test_dict), test_dict))
        elif  not isinstance(test_dict, collections.Mapping):
            raise DeepEqualsError("(Exception: Invalid Types) Expected a Mapping type = {0} but received a {1} type = {2}".format(ref_dict, type_str(test_dict), test_dict))
                
        # by here, both ref_dict and test_dict are Mappings 
        
        if already_seen.is_loop(ref_dict, test_dict):
            return True
        
        ref_keys = ref_dict.keys()
        test_keys = test_dict.keys()
        
        if strict_typing_dict["map_keys"] and len(ref_keys) != len(test_keys):
            raise DeepEqualsError("(Exception: Invalid Keys) Expected dictionary {0} has a different number of keys than received dictionary {1}".format(ref_dict, test_dict))

        if not set(ref_keys).issubset(set(test_keys)):
            return False   # keys don't match
            
        # ref keys are a subset of test keys
        for key in ref_keys:  # recurse through the dictionary
            if not _deep_equal(ref_dict[key], test_dict[key], already_seen):
                return False
        return True
                
        #return operator.eq(sum(_deep_equal(ref_dict[k], test_dict[k]) for k in ref_keys), len(ref_keys))
    
    def _deep_iter_eq(ref_iter, test_iter, already_seen):
        """
        Recursive equality test for iterable elements except dictionaries.
        """
        
        if (strict_typing_dict["iter"] and type(ref_iter) != type(test_iter)):
            raise DeepEqualsError("Expected a {0}  {1} but received {2}  {3}".format(type_str(ref_iter), ref_iter, type_str(test_iter), test_iter))
        elif not isinstance(test_iter, collections.Iterable):
            raise DeepEqualsError("(Exception: Invalid Types) Expected an Iterable type = {0} but received a {1} type = {2}".format(ref_iter, type_str(test_iter), test_iter))
        
        if already_seen.is_loop(ref_iter, test_iter):
            return True
        # Use generalized zip which can handle any sort of iterable.   Note that zip iterable may not have a defined length,
        # so must explicitly iterate through until failure or success.
        for v1, v2 in zip_gen(ref_iter, test_iter):
            if not _deep_equal(v1, v2, already_seen):
                return False
        return True
    
    def _base_eq(ref_value, test_value):
        """
        Equality check for non-recursive (base case) elements.
        The assumption here is that ref_value and test_value are neither dictionaries nor iterables as those are handled elsewhere
        """
        type_ref_value = type(ref_value)
        type_test_value = type(test_value)
        if (type_ref_value != type_test_value):
            #print "Unequal types!"
            if not strict_typing_dict["bool"] and isinstance(ref_value, types.BooleanType):
                return operator.eq(ref_value, bool(test_value))
                
            elif not strict_typing_dict["num"] and type_ref_value in NumberTypes and type_test_value in NumberTypes:
                return float_eq(ref_value, test_value, tol=float_tol)
            
            elif not strict_typing_dict["str"] and type_ref_value in types.StringTypes and type_test_value in types.StringTypes:
                return operator.eq(ref_value.lower(), test_value.lower())
                
            # fall-through should raise exception because not allowed for loose typing 
            raise DeepEqualsError("(Exception: Invalid Types) Incompatible types being compared.  Expected {0}  {1} but received {2}  {3}".format(ref_value, type_str(ref_value), test_value, type_str(test_value)))

        else:    # Both types are the same
            
            if type_ref_value in InexactNumberTypes: 
                return float_eq(ref_value, test_value, tol=float_tol)
            
            elif not strict_typing_dict["str"] and type_ref_value in types.StringTypes:
                return operator.eq(ref_value.lower(), test_value.lower())
            
            elif type_ref_value in DateTimeTypes:
                return date_eq(ref_value, test_value, time_tol)
            
            elif isinstance(ref_value, types.ObjectType):    # Object instances all have type(obj) = <instance> not <SpecificClass>!
                if ref_value.__class__ != test_value.__class__ and strict_typing_dict["obj"]:
                    raise DeepEqualsError("(Exception: Invalid Types) Incompatible classes being compared.  Expected {0}  {1} but received {2}  {3}".format(ref_value, class_str(ref_value), test_value, class_str(test_value)))
                return operator.eq(ref_value,test_value)   # compare if either loose obj typing with unequal classes or strict typing with equal classes 

            
            return operator.eq(ref_value, test_value)

    def _obj_eq(ref_obj, test_obj, already_seen):
        if type(test_obj) != InstanceType:     # OLD STYLE ONLY!!!!
            raise DeepEqualsError("(Exception: Invalid Types) Expected value and type,{0} {1}, but encountered value and type, {2} {3}.".format(ref_obj, type_str(ref_obj), test_obj, type_str(test_obj)))
        
        if already_seen.is_loop(ref_obj, test_obj):
            return True        
        
        if strict_typing_dict["obj"] and not isinstance(test_obj, ref_obj.__class__):
            raise DeepEqualsError("(Exception: Invalid Types) Expected value and type,{0} {1}, but encountered value and type, {2} {3}.".format(ref_obj, class_str(ref_obj), test_obj, class_str(test_obj)))
            
        if hasattr(ref_obj, DEEP_EQUALS_METHOD):
            return getattr(ref_obj, DEEP_EQUALS_METHOD)(test_obj, (lambda ref_val, test_val: _deep_equal(ref_val, test_val, already_seen)))
        elif hasattr(test_obj, DEEP_EQUALS_METHOD):
            return getattr(test_obj, DEEP_EQUALS_METHOD)(ref_obj, (lambda test_val, ref_val: _deep_equal(ref_val, test_val, already_seen)))
        else:
            #logging.info("testing.deep_equal.deep_equal()._obj_eq(): ref_obj = {}, test_obj = {}".format(ref_obj, test_obj))
            return ref_obj == test_obj
        
    def _deep_equal(ref_value, test_value, already_seen):   # TEMPORARY: need to remove default already_seen
        """
        Main recursive deep equality check.   Just dispatches to the appropriate helper function.
        
        already_seen = { "ref": { ref_id: {"ref_val":ref_val, "test_id": test_id, "test_val":test_val}} 
                         "test": { test_id: {"ref_val":ref_val, "ref_id": ref_id, "test_val":test_val}} }
        """
        #logging.info("testing.deep_equal.deep_equal()._deep_equal(): ref_value = {} {}, test_value = {} {}".format(ref_value, type(ref_value), test_value, type(test_value)))
        try:
            is_ref_None = None == ref_value
        except Exception as err:
            raise DeepEqualsError("(Exception: Unable to compare against None) The following exception was thrown when the reference (solution) value was checked for being None: \""+str(err)+"\".   Did you forget to check for None in the reference object's __eq__() method?")
        if is_ref_None:
            return _base_eq(ref_value, test_value)
                
        else:
            if type(ref_value) in types.StringTypes:   # Since strings are also iterable, must process them before the iterable check.
                return _base_eq(ref_value, test_value)
            else:
                if isinstance(ref_value, collections.Mapping):    # Test dictionaries
                    #print "ref_value is a dictionary"
                    return _deep_dict_eq(ref_value, test_value, already_seen)
                elif isinstance(ref_value, collections.Iterable):   # Test iterables
                    #print "ref_value is an Iterable"
                    return _deep_iter_eq(ref_value, test_value, already_seen)
                elif type(ref_value) == InstanceType:
                    return _obj_eq(ref_value, test_value, already_seen)
                else:    
                    # ref_value must be a non-composite
                    return _base_eq(ref_value, test_value)


    #### Start the recursive process  #####
    
    return _deep_equal(ref_val, test_val, _AlreadySeen())



def zip_gen(ref_iter, test_iter):
    """
    Generalized zip generator function for comparing either sequences or non-sequences but not dictionaries.
    Non-sequences must have a definable length and must be uniquely sortable.  Sequences do not have to have
    a definable length.
    
    ref_iter = iterable of reference values
    test_iter = iterable of values to test against the reference values
    
    This function is a generator whose return value can be used as an iterator which iterates through tuples made
    from the corresponding elements of ref_iter and test_iter.  
    
    A TypeError is raised if an attempt is made to zip together a sequence and a non-sequence.
    An IndexError is raised if ref_iter and test_iter have different number of elements.Note that the number of elements is 
    determined by actually traversing the data structures and not by the len() function.   This enables dynamically
    generated sequences to be compared.   
    """
    if not isinstance(ref_iter, collections.Sequence):
        #print str(ref_iter)+" is not a Sequence"
        if not isinstance(ref_iter, collections.Sized):
            TypeError("The non-sequenced {0} {1} reference value cannot be compared against because it does not define a length.".format(ref_iter, type_str(ref_iter))) 
        iter1 = iter(sorted(ref_iter))
        if isinstance(test_iter, collections.Sequence):
            #print str(test_iter)+" is a Sequence"
            raise DeepEqualsError("(Exception: Invalid Types) When comparing against the non-sequenced {0} {1}, encountered the sequenced {2} {3}.".format(ref_iter, type_str(ref_iter), test_iter, type_str(test_iter)))          
        else:
            #print str(test_iter)+" is not a Sequence"
            if not isinstance(test_iter, collections.Sized):
                DeepEqualsError("(Exception: Invalid Types) The non-sequenced {0} {1} value cannot be compared against because it does not define a length.".format(test_iter, type_str(test_iter)))                 
            iter2 = iter(sorted(test_iter))  
    else:   
        #print str(test_iter)+" is a Sequence" 
        iter1 = iter(ref_iter)
        if isinstance(test_iter, collections.Sequence):
            iter2 = iter(test_iter)
        else:
            #print str(test_iter)+" is a Sequence"
            raise TypeError("(Exception: Invalid Types) When comparing against the sequenced {0} {1}, encountered the non-sequenced {2} {3}.".format(ref_iter, type_str(ref_iter), test_iter, type_str(test_iter)))                  
    for x1 in iter1:
        try:
            x2 = iter2.next()
        except StopIteration:
            ref_len_str = ""
            if isinstance(ref_iter, collections.Sized):
                ref_len_str = " ("+str(len(ref_iter))+" elements)"
            test_len_str = ""
            if isinstance(test_iter, collections.Sized):
                test_len_str = " ("+str(len(test_iter))+" elements)"
            raise DeepEqualsError("(Exception: Length Error) When comparing against {0}{1}, the value, {2}{3}, has too few elements.".format(ref_iter, ref_len_str, test_iter, test_len_str))
        yield x1, x2
    #if iter2.next():  <== incorrect result if iterr2.next() returns a zero, empty string, etc
    try:
        iter2.next()
    except StopIteration:
        return  # iter2 should not have any more elements so this is the correct result.
    
    # If no StopIteration was raised, then iter2 has too many elements!        
    ref_len_str = ""
    if isinstance(ref_iter, collections.Sized):
        ref_len_str = " ("+str(len(ref_iter))+" elements)"
    test_len_str = ""
    if isinstance(test_iter, collections.Sized):
        test_len_str = " ("+str(len(test_iter))+" elements)"
    raise DeepEqualsError("(Exception: Length Error) When comparing against {0}{1}, the value, {2}{3} has too many elements.".format(ref_iter, ref_len_str, test_iter, test_len_str))

        
        
def float_eq(ref_val, test_val, tol = 1.0e-10):
    """
    Checks for equality between two numbers to within a specified tolerance. Handles ints, longs, floats and complex.
    ref_val = reference value
    test_val = value being compared against ref_val 
    if tol<0.0, then the given tolerance is treated as an abolute numerical difference
    such that abs(tol) >= abs(ref_val-test_val).  But if tol >= 0.0 (default), the tolerance is interpreted as 
    the allowed percentage error as defined by tol >= abs((ref_val-test_val)/float(ref_val)) 
    If ref_val == 0, then absolute numerical difference is always used.
    Returns True if ref_val and test_val are within the allowed tolerance, returns False otherwise. 
    """
    
    # short circuit the process if Python already thinks they are equal.   
    #This is particularly useful when ref_val = test_val = float('inf') 
    if ref_val == test_val:
        return True   
    
    if tol<0.0 or 0 == ref_val :

        den = 1.0
        tol = abs(tol)
    else:    
        den = cmath.polar(ref_val)[0]   # just want the length.

    return tol >= cmath.polar(ref_val-test_val)[0]/den

    
def date_eq(ref_date, test_date, tol):
    """
    Compares date/time objects.  Returns True if ref_date and test_date are within tol seconds of each other. Returns False otherwise.
    
    Allowed date/time types:  datetime.date, datetime.datetime, datetime.time, datetime.timedelta, time.struct_time 
    ref_date and test_date must be of the same type!
    
    """
    if type(ref_date) != type(test_date):
        raise DeepEqualsError("Incompatible types being compared.  Expected {0}  {1} but received {2}  {3}".format(ref_date, type_str(ref_date), test_date, type_str(test_date)))
    if isinstance(ref_date, datetime.date):   # include datetime.datetime
        t1 = time.mktime(ref_date.timetuple())
        t2 = time.mktime(test_date.timetuple())           
    elif isinstance(ref_date, datetime.time):        
        t1 =time.mktime(datetime.datetime.combine(datetime.date(0,0,0), ref_date).time_tuple())
        t2 =time.mktime(datetime.datetime.combine(datetime.date(0,0,0), test_date).time_tuple())
    elif isinstance(ref_date, datetime.timedelta):
        t1 = ref_date.total_seconds()
        t2 = test_date.total_seconds()
    elif isinstance(ref_date, time.struct_time):
        t1 = time.mktime(ref_date)
        t2 = time.mktime(test_date)
    else:
        raise DeepEqualsError("(Exception: Invalid Types) Unsupported date/time types being compared:  {0}  {1} is being compared against {2}  {3}".format(ref_date, type_str(ref_date), test_date, type_str(test_date)))
    
    return tol >= abs(t1-t2)
 
 

        
# def is_loop(ref_val, test_val, already_seen):
#     """
#     Loop detection utility.  Returns True if an expected loop is detected, i.e. both ref_val and test_val are circular references
#     and test_val is the same reference as was encountered with the previous ref_val.  Returns False if no loop was detected or expected.
#     The function does NOT type check its inputs!   It uses the id(value) for reference comparison.
#     Throws a DeepEqualsError (missing circular reference) if ref_val is a circular reference but test_val is not the same reference 
#     as was previously encountered with the previous ref_val encounter.  Also throws a DeepEqualsError (unexpected circular reference) 
#     if test_val is a circular reference but ref_val is not.  
#     """
#     ref_id = id(ref_val)
#     test_id = id(test_val)
#     if ref_id in already_seen["ref"]:   # ref structure has a loop here
#         if test_id == already_seen["ref"][ref_id]["test_id"]:
#             return True    # structurally correct loop detected.
#         else:    # test structure is not looping when it should
#             raise DeepEqualsError("(Exception: Missing Circular Reference)  A circular reference was expected here.  <br/>Expected <br/>{0} (ID = {1}) <br/>but received <br/>{2} (ID = {3})<br/>Note that the only visible difference may be the value's ID number.".format(already_seen["ref"][ref_id]["test_val"], already_seen["ref"][ref_id]["test_id"], test_val, test_id))
#     elif test_id in already_seen["test"]:
#         raise DeepEqualsError("(Exception: Unexpected Circular Reference)  An invalid circular reference was detected.  <br/>Expected <br/>{0} but found <br/>{1}<br/>Note that difference may not be visible here.".format(already_seen["test"][test_id]["ref_val"], test_val))
#     else:
#         already_seen["ref"][ref_id] = {"test_id": test_id, "test_val":test_val}
#         already_seen["test"][test_id] = {"ref_val":ref_val}
#         return False
                    
def type_str(x):
    """
    Returns an HTML-safe string representation of type(x) which contains angle-brackets that browsers would otherwise 
    interpret as non-printing HTML tags.
    """
    result = cgi.escape(repr(type(x)))
    #print "type_str(", type(x)," = ", result
    return result

def class_str(x):
    """
    Similar to type_str but returns an HTML-safe string representation of x's class.
    """
    return cgi.escape(repr(x.__class__))

##########################################################################
##  Test Utilies for the above code

def _test_zip(ref_iter, test_iter):
    """
    Test utility for zip_gen()
    """
    for a in zip_gen(ref_iter, test_iter):
        print a
    

def _test():
    """
    Test function for deep_equal()
    """
    print "\n****** START TEST ********\n"
    
 
    x = {'a': 'b'}
    y = {'a': 'b'}
    print "True:", x, y, deep_equal(x, y)
    
    x = {'a': 'b'}
    y = {'b': 'a'}
    print "False:", x, y, deep_equal(x, y)
    
    x = {'a': {'b': 'c'}}
    y = {'a': {'b': 'c'}}
    print "True:", x, y, deep_equal(x, y)
    
    x = {'c': 't', 'a': {'b': 'c'}}
    y = {'a': {'b': 'n'}, 'c': 't'}
    print "False:", x, y, deep_equal(x, y)
    
    x = {'a': [1,2,3]}
    y = {'a': [1,2,3]}
    print "True:", x, y, deep_equal(x, y)
    
    x = {'a': [1,'b',8]}
    y = {'a': [2,'b',8]}
    print "False:", x, y, deep_equal(x, y)
    
    x = collections.defaultdict(int)
    x["a"] = 42
    x["b"] = 99
    y = collections.defaultdict(int)
    y["a"] = 42
    try:
        result = deep_equal(x, y)
        print "ERROR should never get here: ", x, y, result
    except Exception as err:
        print "Exception, wrong number of keys: ", x, y, err 
        
    y["b"] = 99
    print "True:", x, y, deep_equal(x, y)

    y["c"] = -1
    try:
        result = deep_equal(x, y)
        print "ERROR should never get here: ", x, y, result
    except Exception as err:
        print "Exception, wrong number of keys: ", x, y, err 
    
    print "True, strict_typing = {'map':False}:", x, y, deep_equal(x, y, strict_typing = {'map':False})
    
    
    y = dict(y)
    print "True, strict_typing = {'map':False}:", x, y, deep_equal(x, y, strict_typing = {'map':False})
     
#     x["z"] = 0
#     x["c"] = -1
#     print "True:", x, y, deep_equal(x, y)
     
    x = 'a'
    y = 'a'
    print "True:", x, y, deep_equal(x, y)

    x = 'abcd'
    y = 'abcd'
    print "True:", x, y, deep_equal(x, y)

    x = 'a'
    y = 'A'
    print "True, strict_typing=False :", x, y, deep_equal(x, y, strict_typing=False)
    
    x = 'abcd'
    y = u'abcd'
    try:
        result =  deep_equal(x, y)
        print "ERROR should not get here!: ", x, y,result
    except Exception as err:
        print "Exception, ASCII vs Unicode types: ", x, y, err
        
    print "True, ASCII vs Unicode, strict_typing={'str':False}:", x, y, deep_equal(x, y, strict_typing={'str':False})
            
    x = 'abCD'
    y = 'aBcd'
    print "False:", x, y, deep_equal(x, y)
    print "True, strict_typing={'str':False}:", x, y, deep_equal(x, y, strict_typing={'str':False})            
            
    x = 'abCD'
    y = u'aBcd'
    print "True, ASCII vs Unicode, strict_typing={'str':False}:", x, y, deep_equal(x, y, strict_typing={'str':False})   
                
    x = 'abcd'
    y = 'abcde'
    print "False:", x, y, deep_equal(x, y)
    
    x = 'abcd'
    y = 'ab'
    print "False:", x, y, deep_equal(x, y)    
    
    x = ['p','n',['asdf']]
    y = ['p','n',['asdf']]
    print "True:", x, y, deep_equal(x, y)
    
    x = ['p','n',['asdf',['xyzzy']]]
    y = ['p', 'n', ['asdf',['yahoo']]]
    print "False:", x, y, deep_equal(x, y)
    
    x = 1
    y = 2
    print "False:", x, y, deep_equal(x, y)

    x = 3.14
    y = 3.14
    print "True:", x, y, deep_equal(x, y)

    x = None
    y = None
    print "True:", x, y, deep_equal(x, y)
    
    x = None
    y = "abc"
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, type error:", x, y, err     

    x = 42
    y = None
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, type error:", x, y, err  
        
    x = 1.000
    y = 1.001
    print "False:", x, y, deep_equal(x, y)

    x = 1.000
    y = 1.001
    print "True: float_tol = 1e-3", x, y, deep_equal(x, y, float_tol=1e-3)

    ## NEED TESTS FOR COMPLEX NUMBERS
    
    x = complex(3, 4)
    y = complex(3, 4)
    
    print "True: ", x, y, deep_equal(x, y)
    
    y = complex(2.1, -5.2)
    print "False: ", x, y, deep_equal(x, y)
    
    y = complex(3.001, 4.001)
    print "False: ", x, y, deep_equal(x, y)
    print "True, float_tol = 1e-3: ", x, y, deep_equal(x, y, float_tol = 1e-3)
    
    x = complex(5, 0)
    y = 5
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, type error:", x, y, err    
    
    print "True, strict_typing=False: ", x, y, deep_equal(x, y, strict_typing=False)
    y = 3
    print "False, strict_typing=False: ", x, y, deep_equal(x, y, strict_typing=False)
    
    
    x1 = (str(p) for p in xrange(10))
    y1 = (str(p) for p in xrange(10))
    
    print "True:", x1, y1, deep_equal(x1,y1)
    #print "True:", x1, y1, deep_equal((str(p) for p in xrange(10)), (str(p) for p in xrange(10)))
    
    
    x = range(4)
    y = range(4)
    print "True:", x, y, deep_equal(x, y)
    
    x= xrange(100)
    y = xrange(100)   
    print "True:", x, y, deep_equal(xrange(100), xrange(100))
    
    x = xrange(2)
    y = xrange(5)
    try:
        result = deep_equal(xrange(2), xrange(5))
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, too many elements:", x, y, err


    x = datetime.datetime.now()
    y = datetime.datetime.now() + datetime.timedelta(seconds=4)
    print "False, default time_tol:",x, y, deep_equal(x, y)

    print "True, time_tol = 5.0:", x, y, deep_equal(x, y, time_tol=5.0) 
    
    x = (1, 2, 3)
    y = [1, 2, 3]
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, wrong type:", x, y, err

    print "True, strict_typing=False:", x, y, deep_equal(x, y, strict_typing=False)
    print "True, strict_typing={'iter':False}:", x, y, deep_equal(x, y, strict_typing={"iter":False})

    x = 42
    y = 42.0
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", x, y, result
    except Exception as err:
        print "Exception, wrong type:", x, y, err

    print "True, strict_typing=False:", x, y, deep_equal(x, y, strict_typing=False)
    print "True, strict_typing={'num':False}:", x, y, deep_equal(x, y, strict_typing={"num":False})
    
    x = set([1,2,3])
    y = set([1,2,3])
    print "True:", x, y, deep_equal(x, y)
    
    x = set([1,2,3])
    y = set([3,1,2])
    print "True:", "set([1,2,3])", "set([3,1,2])", deep_equal(x, y)    
    
    x = set([1,2,3])
    y = set([3,1,0])
    print "False:", x, y, deep_equal(x, y)      
    
    x = set([1,(99, 42),3])
    y = set([1,3, (99, 42)])
    print "True:", "set([1,(99, 42),3])", "set([1,3, (99, 42)])", deep_equal(x, y)

    x = set([1,(99, 42),3])
    y = set([1,3, (99, 43)])
    print "False:", "set([1,(99, 42),3])", "set([1,3, (99, 43)])", deep_equal(x, y)
        
    x = set([1,(99, 42),3])
    y = set([1,3, (99, 42, -1)])
    try:
        result = deep_equal(x, y)
        print "ERROR! Should not get here!:", "set([1,(99, 42),3])", "set([1,3, (99, 42, -1)])", result
    except Exception as err:
        print "Exception, wrong length:", x, y, err
     
    x= [1,(3, 4.0), 5]
    y= (1,[3, 4], 5)
    
    print "True, strict_typing = {'iter':False, 'num':False}: ", x, y, deep_equal(x, y, strict_typing = {"iter":False, "num":False})    
    
    x= [(1, 2), (3, 4), (5, 6)]
    y= [(1,2),(3, 4), (5,6)]
    
    print "True: ", x, y, deep_equal(x, y)    
    
    x= [(1, 2), (3, 4), (5, 6)]
    y= [(1,2),(3, 4), (5,)]
    
    try:
        result = deep_equal(x, y)
        print "ERROR, should not get here!: ", x, y, result   
    except Exception as err:
        print "Exception, length wrong: ", x, y, err         
        
    class MyClass1a():
        pass
    
    class MyClass2a():
        pass    
            
    x = MyClass1a()
    y = x
    print "True, same instance: ", x, y, deep_equal(x, y)
    
    y = MyClass1a()
         
    print "False, different instances: ", x, y, deep_equal(x, y)

    y = MyClass2a()
    
    try:
        result = deep_equal(x, y)
        print "ERROR, shouldn't get here!: ", x, y, result
    except Exception as err:
        print "Exception, wrong class type objects: ", x, y, err

    class MyClass1b():
        def __init__(self, x):
            self.x = x
            
        def get_x(self):
            return self.x       
                    
        def __eq__(self, other):
            if other and hasattr(other, "get_x"):
                return self.x == other.get_x()
            else:   # Need to guard against null input
                return False
    
    class MyClass2b():
        def __init__(self, x):
            self.x = x
    
        def get_x(self):
            return self.x
    
    x = MyClass1b(42)
    y = MyClass1b(42)
         
    print "True: ", x, y, deep_equal(x, y)    

    y = MyClass2b(42)
    try:
        result = deep_equal(x, y) 
        print "ERROR, should never get here!: ", x, y, result  
    except Exception as err:
        print "Exception, wrong class type: ", x, y, err
        
    print "True, strict_typing = {'obj':False}: ", x, y, deep_equal(x, y, strict_typing = {'obj':False})   
    
    x = [1, {"a":MyClass1b(99), "b": (2.0, 4)}, MyClass1b(-33.3)]
    y = [1, {"a":MyClass1b(99), "b": (2.0, 4)}, MyClass1b(-33.3)]
    print "True: ", x, y, deep_equal(x, y)    

    y = [1, {"a":MyClass1b(99.1), "b": (2.0, 4)}, MyClass1b(-33.3)]
    print "False: ", x, y, deep_equal(x, y)
    
    y = [1, {"a":MyClass2b(99), "b": (2.0, 4)}, MyClass1b(-33.3)] 
    print "True, strict_typing=False: ", x, y, deep_equal(x, y, strict_typing=False)  
    
    try:
        result = deep_equal(x, y) 
        print "ERROR, should never get here!: ", x, y, result  
    except Exception as err:
        print "Exception, wrong class type: ", x, y, err        
        

# The above code was inspired by Samuel Sutch's deep_eq() code
# from https://gist.github.com/samuraisam/901117  
# However, the above code is a complete rewrite of the deep_eq() code to the point
# that nothing but the most trivial bits of the original code remains. 
# These modifications are by Stephen Wong  [swong@rice.edu]
# Copyright (c) 2014

# Original deep_eq copyright, included here as a courtesy only:
# Copyright (c) 2010-2013 Samuel Sutch [samuel.sutch@gmail.com]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

