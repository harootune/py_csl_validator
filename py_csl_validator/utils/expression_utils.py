# stdlib
import os
import pathlib
from typing import Union


def find_path_from_caseless(file_path: pathlib.Path) -> Union[pathlib.Path, None]:
    path_lower = pathlib.Path(*[part.lower() for part in file_path.parts]) 
    iter_count = 0
    part_count = len(path_lower.parts)
    checked_path = pathlib.Path('')

    if file_path.is_absolute():
        checked_path.joinpath(path_lower.parts[0])
        iter_count += 1
    
    while iter_count < part_count:
        files = os.listdir(checked_path)
        files_lower = [f.lower() for f in files]

        for i in range(len(files_lower)):
            if files_lower[i] == path_lower.parts[iter_count]:
                checked_path.joinpath(files[i])
                iter_count += 1
                break
        else:
            return None
    
    return checked_path
