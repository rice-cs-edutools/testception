from collections import defaultdict as dd

###---------------------------------------------------
### GLOBAL VARIABLES: 
###---------------------------------------------------
## Valid keywords
SORTED = "sorted"
LOWER = "lower"
UPPER = "upper"
LETTERS = "letters"
DIGITS = "digits"
HEXDIGITS = "hexdigits"

## For varnames being used as the endpoints of a range
START = "start"
END = "end"

## Container types will be stored in an intermediate hashable format
CONTAINER_TYPES = ["dict", "list", "set", "tuple"]
CLASS = "class"

KEYWORDS = dd(list)
KEYWORDS["tuple"] = [SORTED]
KEYWORDS["list"] = [SORTED]
KEYWORDS["str"] = [LOWER, UPPER, LETTERS, DIGITS, HEXDIGITS]
