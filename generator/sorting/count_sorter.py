class CountSorter:
    def __init__(self, config):
        pass

    def sort(self, items):
        return [x[0] for x in sorted(items, key=lambda x: x[1], reverse=True)]
