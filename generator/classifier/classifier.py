from generator.input_name import InputName


class Classifier:
    """
    Gets name with some preprocessing variants.
    Adds information about type of input.
    Adds tokenizations.
    """

    def __init__(self, config):
        pass
    
    def classify(self, name: InputName):
        raise NotImplementedError
