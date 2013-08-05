class Variable :

    InputMode = 'input'
    OutputMode = 'output'
    OptionMode = 'option'

    def __init__(self, name, device, mode=OutputMode, value = False) :
        self.name = name
        self.mode = mode
        self.value = value
        
        if (self.valueType not in [bool, int, float, str]) :
            raise Exception('Invalid defalt value %r for Variable' % value)

    

    
