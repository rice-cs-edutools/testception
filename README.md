Testception is a tool that generates interactive exercises for teaching 
software testing to introductory students. It takes as its input a config
file that includes an inductive specification of a function, a correct 
implementation of that function, and a corpus of (potentially buggy) 
implementations of that function. 

Given these inputs, Testception then generates a semi-exhaustive base test
set, executes the base tests on the corpus, and selects and sequences a 
subset of the corpus in order of increasing "difficulty of testing" (~the 
number of bugs found during testing). These programs can then be provided
to students as feedback as they work to develop their own test suites.

Testception was developed at Rice University by Rebecca Smith, Terry Tang, 
Joe Warren, and Scott Rixner. It is freely-distributable open-source software, 
released under GNU GPL v3.0. It is written in Python 2, and compatible with 
Python 2 programs.

# Defining a Project & Its Functions

1. Add any provided files which implementations of this project are expected 
   to import to a single directory <import_dir>.

2. Add any student solutions which implement this project to a single 
   directory <student_dir>.

3. Create a new subdirectory in ./projects named project\<projno>, where 
   \<projno> is an integer.

4. Within the ./project/project\<projno> subdirectory, create the following 
   files:

   1. `description.py`: must define the following variables:
      * projectname - a string
      
      * funclist - a list of strings, where each is the name of a function in
        this project
      
        **NOTE**: methods are not currently supported; however, functions that
        take class instances as parameters are

   2. `solution.py`: must contain a correct implementation of each function
      in funclist.

   3. For each function f in funclist, create a config file func\<funcno>.cfg, 
      where \<funcno> is an integer corresponding to its index in funclist. 

           --------------------------------------------------------------
           Each config file must include the following required sections:
           --------------------------------------------------------------
           [types]
           Defines the parameter types for this function. Each parameter type 
           must be defined on a separate line.

           The grammar for specifying paramtypes is as follows:
           -------------------------------------------------------
           *NOTE: In defining the grammar rules, terminal symbols are 
           surrounded by quotation marks so as to clearly indicate required 
           spacing; however, the quotation marks themselves should not appear 
           in the config file except when surrounding <strval>s.

           <paramtype> ::= <nonclasstype>
                         | <classtype>

           <nonclasstype> ::= <simpletype> 
                            | <grouptype> "(" <paramtype> ")"
                            | <maptype> "(" <paramtype> ":" <paramtype> ")"

           <simpletype> ::= "int" | "float" | "bool" | <strtype> 

           <strtype> ::= "str"
                       | <string> " str"
                       | "lower str"
                       | "upper str"
                       | "letters str"
                       | "digits str"
                       | "hexdigits str"

           <grouptype> ::= "list" | "tuple" | "set"
                         | "sorted list" | "sorted tuple"

           <maptype> ::= "dict"

           <classtype> ::= "class" <strval> { "\n" <fieldtype> } ; <strval> is
                                                                   the class 
                                                                   name

           <fieldtype> ::= "    " <strval> " " <nonclasstype> ; <strval> is the
                                                                field* name, 
                                                                <nonclasstype>
                                                                is its type

           <strval> ::= any valid Python string (surrounded by quotation marks)

           *NOTE: Keywords preceeding " str" in the <strtype> rule are used
           to restrict the domain of characters for string generation. An
           arbitary string <strval> can be used to restrict the domain to a
           custom subset of characters, while "lower", "upper", "letters",
           "digits", and "hexdigits" use the corresponding variables defined
           in Python's string module (i.e., string.lower, string.upper, etc.)

           *NOTE: For parameters that are objects, note that FIELDS, NOT 
           parameters to the constructor, must be defined.

           [exhaustive domain]
           Defines the domain for exhaustive test case generation. There must 
           be one line corresponding to each parameter type.

           The grammar for specifying domains is as follows:
           ----------------------------------------------------
           <domain> ::= <nonclassdom>
                      | <classdom>

           <nonclassdom> ::= <simpledom> 
                           | <groupdom> "(" <domain> ")"
                           | <mapdom> "(" <domain> ":" <domain> ")"

           <simpledom> ::= <intdom> | <floatdom> | <booldom> | <strdom>

           <intdom> ::= <intval>"-"<intval>
                      | <intlist>
                      | <variable> 
                      | <intval>"-"<variable> 
                      | <variable>"-"<intval>

           <floatdom> ::= <floatval>"-"<floatval>
                        | <floatlist>

           <strdom> ::= <intdom>   ; represents the range of allowable lengths
                      | <strlist>

           <booldom> ::= any

           <groupdom> ::= <intdom> ; represents the range of allowable lengths

           <floatlist> ::= "[" <floatval> { "," <floatval> } "]"
           <strlist> ::= "[" <strval> { "," <strval> } "]"
           <intlist> ::= "[" <intval> { "," <intval> } "]" ; represents a 
                                                             discrete set of
                                                             allowable values
           <classdom> ::= "class" <string> { "\n" <fielddom> } ; <string> is
                                                                 the class name

           <fielddom> ::= "    " <strval> " " <nonclassdom> ; <strval> is the
                                                              field name, 
                                                              <nonclassdom>
                                                              is its domain
           <intval> ::= any valid positive Python int
           <floatval> ::= any valid positive Python float
           <strval> ::= any valid Python string (surrounded by quotation marks)
           <variable> ::= <strval>  ; used to define more sophisticated 
                                      relationships between arguments, see
                                      optional sections below

           [random domain]
           Defines the domain for randomized test case generation. Uses the 
           same grammar as [exhaustive domain].

           [num random]
           Defines the number of random test cases to be generated, n >= 0.

           --------------------------------------------------------------
           Config files may also contain the following optional sections:
           --------------------------------------------------------------
           [exhaustive validation]
           Points to a validation function vf to be applied to the exhaustive 
           tests e_tests. The validation function will be used to filter out 
           invalid test cases (filter(vf, e_tests)); thus, its parameters must 
           be identical to those of f, and it must return a bool (True for
           valid; False otherwise).
           
           Validation functions are specified as follows:
           -------------------------------------------------
           <filename.py>, <funcname>

           where <filename.py> is the name of the file in the 
           ./base_set_generation/validation subdirectory where the validation
           function is defined, and <funcname> is the name of that function.

           [random validation]
           Points to a validation function vf to be applied to the random 
           tests. Uses the same format as [exhaustive validation].

           [variables]
           Used to define more sophisticated relationships between arguments. 
           Variables are a less expressive means of validation, but offer the
           advantage of providing pruning *during* generation rather than 
           filtering after-the-fact, which can substantially decrease 
           generation time.

           The grammar for specifying variables is as follows:
           ------------------------------------------------------
           <variable> ::= <strval> " " <intval>"-"<intval> ; <strval> is the name,
                                                             <intval>-<intval> 
                                                             is the range of
                                                             allowable values
           <intval> ::= any valid Python int
           <strval> ::= any valid Python string (surrounded by quotation marks)

           See the contents of the ./projects/examples directory for examples.

           [constructors] 
           If any parameters are classes, this points to the constructor for
           that class and defines dummy arguments for initialization. Dummy
           arguments can be any valid arguments; all fields will ultimately be
           overwritten with generated values.

           Constructors are specified as follows:
           --------------------------------------------
           <filename.py>, <classname>
               <arg0 initval>
               ...
               <argN initval>

           where <filename.py> is the name of the file in the <import_dir>
           where the class is defined, <classname> is the name of the class,
           and <argN initval> uses Python syntax to define a literal initial
           value for the Nth argument to the constructor.

# Generating Test Exercises for a Function

1. (Re-)generate the menu of options based on the updated contents of the 
   ./projects directory:

       python ./run.py updatemenu

   After the update, the menu will be displayed, including the names and 
   indices of all projects and functions. It can be re-displayed at any time
   using the command:

       python ./run.py showmenu

2. From the menu, identify the \<projno> and \<funcno> for which to generate
   test exercises. Exercise generation involves several steps, each of 
   which depends on the output of the previous step:

   1. Gather corpus of implementations. If using student solutions,
      all files should be placed in a single directory \<studentdir>.
      Implementations of a given function should then be extracted
      from those files. The extraction process will separate 
      individual functions and strip out extra unwanted code that could
      slow the testing process. Stripped-down versions will be stored
      in ./extracted_files/proj\<projno>_func\<funcno>.

           Required command and arguments:
           python ./run.py extract -p <projno> -f <funcno> -s <student_dir>

           Optional flags:
           -i <import_dir>

       Use <funcno> < 0 to extract all functions for the given project.

       A mutation tool, such as mutpy, may be used in place of, or in
       addition to, extraction to generate implementations. Mutant files 
       should be placed in ./extracted_files/proj\<projno>_func\<funcno>.

    2. Generate the base test set used to identify bugs within the 
       corpus of implementations. Output will be placed in 
       ./base_set_generation/output/proj\<projno>_func\<funcno>.py.

           Required command and arguments:
           python ./run.py gen -p <projno> -f <funcno>

           Optional flags:
           -i <import_dir>

    3. Identify bugs within the corpus of implementations. Output will
       be placed in ./test_output/proj\<projno>_func\<funcno>.pickle.

           Required command and arguments:
           python ./run.py test -p <projno> -f <funcno>

           Optional flags:
           -i <import_dir>

    4. Select and order the subset of implementations to be displayed to
       students as they progress through the exercise. Output will be 
       placed in ./output/proj\<projno>_func\<funcno>.py.

           Required command and arguments:
           python ./run.py pick -p <projno> -f <funcno>

           Optional flags:
           -i <import_dir>

   If all of the above steps are desired, use the "all" command:
   
       python ./run.py all -p <projno> -f <funcno> -s <student_dir>

       Optional flags:
       -i <import_dir>

3. Create the evaluation file for the function to be tested. This can be based
   off the example in ./evaluation/instructor_template.py; search for **TODO**
   within that file for all spots that must (or may) be customized to the 
   function in question.

# Dependencies

* radon v1.4.2 (https://pypi.python.org/pypi/radon/1.4.2)
