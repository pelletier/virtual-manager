"""
This script returns you the directory of a VM.
You can wrap it in a shell function and thus create a `vmcd` function, which
allows you to move to the directory of a VM.
"""

import sys
from vms import cd
from utils import nostdout

try:
    name = sys.argv[1]
except IndexError:
    sys.exit(-1)

with nostdout():
    path = cd(name)
print path
