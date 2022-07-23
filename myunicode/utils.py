from typing import Tuple, List, Optional

def load_ranges(path: str) -> Tuple[List[int], List[Optional[str]]]:
    starts = [0]
    names = [None]

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue

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
