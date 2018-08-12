from aquavalet.core import exceptions

def require_group(match, group_name, message=''):
    groupdict = match.groupdict()
    group = groupdict.get(group_name)
    if group:
        return group
    else:
        raise exceptions.InvalidPathError(message)