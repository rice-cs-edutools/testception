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
import astor
import errno
import hashlib
import os
import progress.bar
import subprocess

class RemoveDocstrings(ast.NodeTransformer):
    """
    Node transformer to remove docstrings from AST.
    """
    def strip_docstring(self, node):
        """
        If the first child node is a string, assume it
        is the docstring and strip it.
        """
        self.generic_visit(node)
        if (isinstance(node.body[0], ast.Expr)):
            expr = node.body[0].value
            if (isinstance(expr, ast.Str)):
                if len(node.body) > 1:
                    node.body.pop(0)
                else:
                    ## Empty definition, just clear string
                    node.body[0].value.s = ""
        return node

    def visit_FunctionDef(self, node):
        return self.strip_docstring(node)

    def visit_ClassDef(self, node):
        return self.strip_docstring(node)

    def visit_Module(self, node):
        return self.strip_docstring(node)

class FindHelpers(ast.NodeVisitor):
    """
    Helper class for finding helper functions employed by top-level function 
    being extracted.
    """
    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self._helper_names = set([])

    def visit_Call(self, node):
        try:
            self._helper_names.add(node.func.id)
        except:
            pass

        ast.NodeVisitor.generic_visit(self, node)

    def get_names(self):
        return self._helper_names

class FindImports(ast.NodeVisitor):
    """
    Helper class for finding import statements.
    """
    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self._imports = []

    def visit_ImportFrom(self, node):
        import_str = "from " + node.module + " import " 
        for name in node.names:
            import_str += name.name
        self._imports.append(import_str)

    def visit_Import(self, node):
        for name in node.names:
            import_str = "import " + name.name
            if name.asname:
                import_str += " as " + name.asname
            self._imports.append(import_str)

    def get_imports(self):
        return self._imports

class FindFxn(ast.NodeVisitor):
    """
    Helper class for finding top-level function definition.
    """
    def __init__(self, fxnname):
        ast.NodeVisitor.__init__(self)
        self._fxnname = fxnname
        self._found = False
        self._fxnnode = None

    def visit_Module(self, node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) and (child.name == self._fxnname):
                self._found = True
                self._fxnnode = child
                break

    def has_fxn(self):
        return self._found

    def get_fxn(self):
        return self._fxnnode

class RemoveTopLevelCalls(ast.NodeTransformer):
    """
    Node transformer to remove top level function calls in a module.
    """
    def visit_FunctionDef(self, node):
        return node

    def visit_ClassDef(self, node):
        return node

    def visit_Lambda(self, node):
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            newname = ast.Name("None", ast.Load())
            node.value = newname
            return node
        else:
            self.generic_visit(node)
            return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            newname = ast.Name("None", ast.Load())
            node.value = newname
            return node
        else:
            self.generic_visit(node)
            return node

    def visit_Call(self, node):
        newname = ast.Name("None", ast.Load())
        return newname

def get_last(line):
    words = line.split()
    return words[-1]

def is_pyfile(filename):
    if filename.endswith(".py"):
        return True
    else:
        return False

def main(inputdir, outputdir, funcnos, funcnames,
    funconly=False, funcplushelpers=True, savedfilelist=""):
    """
    inputdir - name of input directory
    outputdir - name of output directory
    funcname  - name of function of interest
    funconly  - boolean indicating if only function should be extracted
    funcplushelpers - boolean indicating if only function + its helper functions should be extracted
    savedfilelist - name of JSON file containing list of files to extract from
                    if empty string, then ignored
    """
    ## Create output directory
    for funcno in funcnos:
        try:
            os.makedirs(outputdir + str(funcno))
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

    s = subprocess.Popen("ls -l " + inputdir,
                         shell=True,
                         stdout=subprocess.PIPE)
    listing = s.communicate()[0]
    lines = listing.split('\n')
    lines = lines[1:-1]
    files = map(get_last, lines)

    filenames = filter(is_pyfile, files)
    filenames = [os.path.abspath(inputdir) + "/" + filename 
        for filename in filenames]

    bar = progress.bar.ChargingBar("   -- Extracting", 
        max=len(filenames))
    
    fname_to_codestr = {}
    funchashset = {}

    numdups = [0]*len(funcnos)
    numunique = [0]*len(funcnos)
    numbadfilesfunc = [0]*len(funcnos)

    for filename in filenames:
        bar.next()
        ## Read the file
        pyfile = open(filename)
        pystr = pyfile.read()

        for idx in range(len(funcnos)):
            funcno = funcnos[idx]
            funcname = funcnames[idx]

            outfilename = outputdir + str(funcno) + "/" + funcname + "_" \
                + filename[filename.rfind("/")+1:]

            ## Parse the file; must be in try/except, as may not be parseable
            try:
                tree = ast.parse(pystr)
            except Exception as err:
                numbadfilesfunc[idx] += 1
                continue

            codestr, codestr_no_imports = extract(tree, funcname, \
                funconly, funcplushelpers, filename, set([]))
            if not codestr:
                continue

            ## Hash the function using md5 to eliminate duplicates
            codehash = hashlib.md5(codestr_no_imports).hexdigest()
                
            if codehash in funchashset:
                ## We have already seen this implementation
                numdups[idx] += 1

                ## Take the longest one to ensure we get all imports
                if len(codestr) > len(fname_to_codestr[funchashset[codehash]]):
                    del fname_to_codestr[funchashset[codehash]]
                    funchashset[codehash] = outfilename
                    fname_to_codestr[outfilename] = codestr

                continue

            funchashset[codehash] = outfilename
            fname_to_codestr[outfilename] = codestr
            numunique[idx] += 1

            for outfilename, codestr in fname_to_codestr.items():
                ## Write to a file
                outf = open(outfilename, "w+")
                outf.write(codestr)
                outf.close()

    for idx in range(len(funcnos)):
        print "\n      Funcname:", funcnames[idx]
        print "      Dups:", numdups[idx]
        print "      Unique:", numunique[idx]
        print "      Bad files with func:", numbadfilesfunc[idx]

    bar.finish()

def extract(tree, funcname, funconly, funcplushelpers,  
    filename, helper_names):
    """
    Extract the given function from the given AST.
    """
    codestr_no_imports = ""
    codestr = ""

    ## Look for the function node 
    finder = FindFxn(funcname)
    finder.visit(tree)
    found = finder.has_fxn()

    import_finder = FindImports()
    import_finder.visit(tree)

    importstr = ""
    if not helper_names:
        for import_str in import_finder.get_imports():
            importstr += import_str + "\n"
        importstr += "\n"

    if found: 
        ## Found the function
        if funconly or funcplushelpers:
            ## Only extract function
            node = finder.get_fxn()
        else:
            ## Extract entire module without top level calls
            node = RemoveTopLevelCalls().visit(tree)

        ## Remove docstrings
        node = RemoveDocstrings().visit(node)

        ## Convert the modified module to source code string
        codestr = importstr + astor.to_source(node)
        codestr_no_imports = astor.to_source(node)

        ## Extract all helper functions
        if funcplushelpers:
            subtree = ast.parse(codestr)
            helper_finder = FindHelpers()
            helper_finder.visit(subtree)
            names = helper_finder.get_names()
            new_helper_names = names.difference(helper_names)
            helper_names = helper_names.union(new_helper_names)

            for helper_name in new_helper_names:
                helper_codestr, helper_codestr_no_imports = \
                    extract(tree, helper_name, \
                    funconly, funcplushelpers, \
                    filename, helper_names)
                if helper_codestr:
                    codestr = codestr + "\n\n" + helper_codestr 
                    codestr_no_imports = codestr + "\n\n" + helper_codestr_no_imports

        ## Compile it to check for errors, should be in try/except
        try:
            codeco = compile(codestr, filename, 'exec')
        except:
            ## File doesn't compile
            print "      Error compiling transformed file from", filename
            return "", ""

    return codestr, codestr_no_imports
