from typing import Tuple, List, Optional, Iterable


def get_data_lines(lines: Iterable[str]) -> Iterable[str]:
    """
    Remove leading/trailing whitespace,
    ignore empty and commented-out lines (#).
    """
    lines = map(str.strip, lines)
    return (l for l in lines if len(l) > 0 and not l.startswith('#'))


def load_ranges(path: str) -> Tuple[List[int], List[Optional[str]]]:
    """
    For a file with the following format:
    START_CODE;STOP_CODE;NAME
    load a list of ranges for use with bisect.
    Gaps are represented as ranges with name=None.
    """
    starts = [0]
    names = [None]

    with open(path, 'r') as f:
        for line in get_data_lines(f):
            fields = line.split(';')
            start = int(fields[0], base=16)
            stop = int(fields[1], base=16)
            name = fields[2].strip()

            # check if there is a gap between the last range and this one
            if starts[-1] == start:  # no gap
                # overwrite previous None range
                # and remove the gap
                names[-1] = name
            else:  # gap
                # insert new range after previous None range
                # keeping the gap
                starts.append(start)
                names.append(name)

            # assume that this range is the last one
            # and insert a None range
            starts.append(stop + 1)
            names.append(None)
    
    return starts, names
