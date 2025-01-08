try:
    # import could fail if package not installed
    from suffixtree import SuffixQueryTree
    # building could fail if the arch is incompatible
    SuffixQueryTree(False)
    HAS_SUFFIX_TREE = True
except Exception:
    # make sure the name can be imported
    SuffixQueryTree = None
    HAS_SUFFIX_TREE = False
