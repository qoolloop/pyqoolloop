

class NamedFields:
    """
    A class that can have its fields initialized
    """

    def __init__(self, **kwargs):
        """
        Initializer

        :param kwargs: fields and values to be set in this instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # endfor
