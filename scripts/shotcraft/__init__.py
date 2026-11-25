"""shotcraft: a production crew for AI content (Python 3.9+, standard library only).

Shared names every module may import:
    VERSION                      the plugin's code version
    ShotcraftError               an error: sc.py prints it and exits 1
    Refused(ShotcraftError)      a gate said no: sc.py prints the reason and exits 2
"""

VERSION = "0.2.0"


class ShotcraftError(Exception):
    """Something went wrong (bad input, missing file). sc.py exits 1."""


class Refused(ShotcraftError):
    """A rule or gate refused the action. sc.py exits 2 and prints the reason."""
