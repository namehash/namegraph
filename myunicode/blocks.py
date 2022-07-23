def _load_blocks():
    starts = [0]
    names = [None]

    with open('data/myunicode/Blocks.txt', 'r') as f:
        for line in f:
            fields = line.split(';')
            start = int(fields[0], base=16)
            stop = int(fields[1], base=16)
            name = fields[2].strip()

            # check if there is a gap between the last block and this one
            if starts[-1] == start:  # no gap
                # overwrite previous None block
                # and remove the gap
                names[-1] = name
            else:  # gap
                # insert new block after previous None block
                # keeping the gap
                starts.append(start)
                names.append(name)

            # assume that this block is the last one
            # and insert a None block
            starts.append(stop + 1)
            names.append(None)
    
    return starts, names


BLOCK_STARTS, BLOCK_NAMES = _load_blocks()
