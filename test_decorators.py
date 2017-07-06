from decorators import pass_args


def _pass_args_function(arg0=0, arg1=1, arg2=2, kwargs=None):

    def _check_argument(name, value, default_value, kwargs):
        assert ((name not in kwargs) and (value == default_value)) or \
            (kwargs[name] == value)
    
    _check_argument("arg0", arg0, 0, kwargs)
    _check_argument("arg1", arg1, 1, kwargs)
    _check_argument("arg2", arg2, 2, kwargs)


@pass_args
def pass_args_function(arg0=0, arg1=1, arg2=2, kwargs=None):
    _pass_args_function(arg0, arg1, arg2, kwargs)


def test_pass_args_to_function():
    
    pass_args_function()
    pass_args_function("a")
    pass_args_function("a", "b")
    pass_args_function(arg1="b")
    pass_args_function(arg2="c")
    pass_args_function(arg0="a", arg1="b")
    pass_args_function(arg0="a", arg1="b", arg2="c")


@pass_args
class PassArgsClass:

    def __init__(self):
        # args won't be passed to __init__()
        pass


    def func(self, arg0=" ", kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)
        

def test_pass_args_to_class():

    instance = PassArgsClass()

    instance.func(arg0="A")
    instance.func("A")
