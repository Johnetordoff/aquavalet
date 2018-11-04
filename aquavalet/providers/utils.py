import re
from aquavalet import exceptions


def require_group(match, group_name, message=''):
    groupdict = match.groupdict()
    group = groupdict.get(group_name)
    if group:
        return group
    else:
        raise exceptions.InvalidPathError(message)


def require_match(pattern, string, message=''):
    match = re.match(pattern, string)
    if match:
        return match
    else:
        raise exceptions.InvalidPathError(message)

