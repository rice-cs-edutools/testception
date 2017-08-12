## TODO: update the following assignment description
"""
<h3>
    Assessment of test case coverage for <code>[TODO: function name]()</code>
</h3> 
<p>
    A machine test that automatically assesses the completeness of a list of 
    provided test cases for the <code>[TODO: function name]()</code> function.
<p>
    The <code>[TODO: function name]()</code> function takes as its input 
    [TODO: thorough description of parameter types, domains, and meanings].
<p>
    Your input file should contain a single Python definition:
    <ul>
    <li>
        A list <code>TEST_CASES</code> containing at most <b>[TODO: max number 
        of test cases] test cases</b> for the function
        <code>[TODO: function name]()</code>.
    </li>
    <li>
        Each test case in this list should be a list of tuples of length 
        [TODO: number of parameters] whose entries are [TODO: brief description
        of parameter types and domains].
    </li>
    </ul>
    These tuples will be used as the input to 
    <code>[TODO: function name[()</code>.  You do not need to provide the 
    corresponding (expected) output. We will compute it from our reference 
    implementation. Note that submissions to Testception that do not conform 
    to this format are rejected.
<p>
    Testception will assess the completeness of the test cases in 
    <code>TEST_CASES</code> using a hidden suite of incorrect implementations 
    of <code>[TODO: function name]()</code> that we have compiled. 
    Specifically, Testception will run each of these incorrect implementations
    on the test cases in <code>TEST_CASES</code>. If an incorrect 
    implementation returns a correct answer on all tests in 
    <code>TEST_CASES</code>, Testception will record that the program 
    (incorrectly) passed the provided tests. If an incorrect implementation 
    returns an incorrect answer on at least one of the tests in 
    <code>TEST_CASES</code>, Testception will record that the implementation 
    (correctly) failed the provided tests.
<p>
    The grade that you receive for this exercise will depend on the number of
    incorrect implementations that failed the provided tests.  Therefore, to
    maximize your score on this exercise, your goal should be to construct a
    list of tests that maximize the number of programs that fail your provided
    tests. In constructing this list, you should try to target each distinct
    logical category of input. In particular, try to identify "edge cases"
    involving unusual or extreme values for one or more inputs.
"""

# ------------- Imports and other initialization -------------
import os
import imp
import sys
import math
import json			
import types
import random
import unittest

## TODO: update the following line to import a student's submission
import sample_student_submission as student_submission

## The point value for this assignment
## TODO: update as desired
MAX_SCORE = 50
TEST_INFO = { 
    "total_score" : 50
}

## TODO: tune MAX_TEST_CASES to the function being tested to prevent students
## from just trying to test things exhaustively

## The maximum allowable number of tests in a students' submitted test suite
MAX_TEST_CASES = 12

## TODO: optionally tune GRADE_RANGES to the function being tested; 
## alternatively, set CUSTOM_SCORING_ENABLED = False

## Optional custom scoring scale that identifies key "threshold" points
## (in this example: 24, 26, 45, 49, 54, 56, 57, ...) beyond which the 
## students' test suites are considered to be substantively better. 
## Improvement within the same range will result in a very minor increase
## in score, while jumping across a threshold will result in a more 
## substantial increase in score. See score() function for more detail.
GRADE_RANGES = [range(24, 26), range(26, 45), range(45, 49), range(49, 54),
                range(54, 56), [56], range(57, 59), range(59, 61), [61], [62],
                [63], [63], [65], [66], [67], [68], [69], [70], [71]]

CUSTOM_SCORING_ENABLED = False

## TODO: replace INCORRECT_FUNCS with the contents of 
## output/proj<projno>_func<funcno>.py

## Incorrect solutions to be tested, ordered from "easiest" (most failures) 
## to "hardest" (most passes)
funcs = [["\ndef add(inp1, inp2):\n    return inp1"],
         ["\ndef add(inp1, inp2):\n    return inp1 - inp2"]]

INCORRECT_FUNCS = funcs

## TODO: replace the following with a correct implementation of the function
## to be tested

## Correct implementation of add()
def correct_solution(inp1, inp2):
    return inp1 + inp2

class TestceptionTestCase(unittest.TestCase):
    """
    Machine grading code for [TODO: function name]() test assessment,

    The unit tests will always "fail" with a message string that is
    a JSON-encoded Python dictionary with two keys: the string "pts"
    and the string "msg".  

    The value of "pts" will be the deduction from the maximum score
    (TEST_INFO["total_score"]).  So, if the student was able to get all
    incorrect programs to fail at least one of their tests, the value of "pts"
    would be 0.

    The value of "msg" will be the feedback that should be presented to
    the student.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the testing class. Any input parameters are passed to the 
        superclass constructor.
        """
        ## Generic superclass constructor call
        unittest.TestCase.__init__(self, *args, **kwargs)

    def validate(self):
        """
        Validate the test set provided by the student.

        TODO: update the input validity checking
        """
        deduction = TEST_INFO["total_score"]

        ## Check whether a list TEST_CASES is provided
        try:
            student_test_cases = student_submission.TEST_CASES
        except:
            msg_dict = {"pts": -deduction, "msg": "Test cases rejected. " + \
                "Required definition for TEST_CASES not found."}            
            self.fail(json.dumps(msg_dict))

        if type(student_test_cases) != types.ListType:
            msg_dict = {"pts": -deduction, "msg": "Test cases rejected. " + \
                "TEST_CASES is not a list."}            
            self.fail(json.dumps(msg_dict))

        ## Check whether the length of TEST_CASES is acceptable            
        if len(student_test_cases) > MAX_TEST_CASES:
            msg_dict = {"pts": -deduction, "msg": "Test cases rejected. " + \
                "TEST_CASES is not a list of length " + str(MAX_TEST_CASES) + \
                " or less."}
            self.fail(json.dumps(msg_dict))

        ## TODO: update the following to check that the contents of each test
        ## case comply with the specified parameter types and domains of the
        ## function being tested

        ## Check the validity of each test case
        for test_case in student_test_cases:

            ## Each test case = a tuple containing three card vales
            if (type(test_case) != types.TupleType):
                msg_dict = {"pts": -deduction, "msg": "Test cases " + \
                    "rejected. TEST_CASES is not a list of tuples."}
                self.fail(json.dumps(msg_dict))

            ## Each tuple must be length three
            if len(test_case) != 2:
                msg_dict = {"pts": -deduction, "msg": "Test cases " + \
                    "rejected. TEST_CASES is not a list of tuples of " + \
                    "length two."}
                self.fail(json.dumps(msg_dict))

            ## Each tuple should contain only integers
            for elem in test_case:
                if type(elem) != types.IntType:
                    msg_dict = {"pts": -deduction, "msg": "Test cases " + \
                        "rejected. TEST_CASES is not a list of tuples of " + \
                        "integers."}
                    self.fail(json.dumps(msg_dict))

        return student_test_cases

    def test_completeness(self):
        """
        Analyze coverage of student-provided test set.

        TODO: change the function name in the indicated locations
        """
        ## Validate test cases
        student_test_cases = self.validate()

        ## Silence stdout during testing
        saved_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

        ## Test coverage of student-provided test set, by counting how many
        ## of the incorrect solutions in PM_FUNCS the student fails.
        ## High failure count => high coverage.
        num_caught = 0
        first_false_pos = -1

        for idx in range(len(INCORRECT_FUNCS)):
            func = INCORRECT_FUNCS[idx][0]

            ## Set up the incorrect solution to be tested; running exec on this
            ## code snippet will define the "blackjack3" function to be used 
            mod = imp.new_module("student")
            exec func in mod.__dict__

            failed = False
            for test_case in student_test_cases:
                try:
                    ## TODO: replace "add" with the name of the 
                    ## function being tested

                    ## Run case through incorrect solution; may fail, since 
                    ## solution is known to be incorrect
                    computed = mod.add(*test_case) 

                    ## Run case through correct solution and see if case 
                    ## (correctly) identifies func as incorrect
                    expected = correct_solution(*test_case)

                    if expected != computed: 
                        failed = True

                except:
                    failed = True

            if failed:
                ## Student test set correctly identified this func as incorrect
                num_caught += 1

            ## Keep track of the least-complex function that the student
            ## failed to catch
            elif first_false_pos == -1:
                first_false_pos = idx

        ## Restore stdout
        sys.stdout = saved_stdout

        ## Prepare "error" message, which is actually used to report results
        error_message = "TEST CASES successfully assessed."
        if first_false_pos != -1:
            error_message += "\n\nThe following incorect implementation(s) " \
                + "of [TODO: function name]() (#" + str(first_false_pos) \
                + ") contain(s) errors not detected by your test cases:\n\n"
            for func in INCORRECT_FUNCS[first_false_pos]:
                error_message += func + "\n--------------------------------------------\n"
        else:
            error_message += "\nCongratulations! Your test suite " \
                + "successfully catches all incorrect implementations.\n"

        if CUSTOM_SCORING_ENABLED:
            grade = self.score(num_caught)
        else:
            grade = (float(num_caught)/len(INCORRECT_FUNCS))*MAX_SCORE

        deduction = MAX_SCORE - grade
        msg_dict = {"pts": -deduction, "msg": error_message} 
        self.fail(json.dumps(msg_dict))

    def score(self, num_caught):
        """
        Convert number of caught programs to a score between 0 and MAX_SCORE.
        """
        if num_caught < GRADE_RANGES[0][0]:
            width = float(GRADE_RANGES[0][0])
            dist_from_min = num_caught
            idx = -1

        else:
            for idx in range(len(GRADE_RANGES)):
                if num_caught in GRADE_RANGES[idx]:
                    break

            if idx == len(GRADE_RANGES):
                idx = -1 

            width = float(len(GRADE_RANGES[idx]))
            dist_from_min = num_caught - GRADE_RANGES[idx][0]

        score = (idx + 1 + (dist_from_min / width)) * \
            (float(MAX_SCORE)/len(GRADE_RANGES))
        return score


# -------------- Code to simulate AppEngine unit tester ----------------
def test():
    my_suite = unittest.TestLoader().loadTestsFromTestCase(TestceptionTestCase)
    unittest.TextTestRunner().run(my_suite)    

## TODO: update as needed for use with your scoring framework
test()
