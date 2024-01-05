''' Module that gets run when the package is referenced in an import (dont do this)
  Its designed so that it automatically finds all ResponseInterface classes when
  'from lib.Responses import *' is run at the top level.
  TBD if this is gonna break stuff but its cool and im fucking with it so idc.'''

from os import path
import glob
import re
from .response import ResponseInterface

# Get a list of all the other python files in this directory (and strip the .py)
fileglob = glob.glob(path.join(path.dirname(__file__), "*.py"))
files = [ f for f in fileglob if path.isfile(f) and not f.endswith('__init__.py')]

# Read file text to find classes that inheret ResponseInterface
responses = []
for filename in files:
  with open(filename, 'r') as file:
    classes = re.findall('class (\w+)\(ResponseInterface', file.read())
  
  if classes:
    module = path.basename(filename)[:-3] # Name of file, without .py
    responses += [(module, cls) for cls in classes]

# Dynamically import all the other Responses
for response in responses:
  exec('from .{} import {}'.format(*response))