import datetime

class Rule(object) :

    def __init__(self, controller) :
        self.controller = controller
        self.inputConnections = {}
        self.outputConnections = {}
        self.options = self.GetDefaultOptions()

    def Init(self) :
        pass

    def GetOption(self, optionName) :
        return self.options[optionName]

    # Return a list of strings, each of which identifies
    # an input that this device can provide a value for
    def GetInputNames(self) :
        return []

    # Return a list of strings, each of which identifies
    # an output that this device can receive a value for
    def GetOutputNames(self) :
        return []

    # Return a dictionary with the default options for
    # this device
    def GetDefaultOptions(self) :
        return {}

    def GetInput(self, inputName) :
        if (inputName not in self.inputConnections) :
            return None
        deviceName,varName = self.inputConnections[inputName]
        return self.controller.Get(deviceName, varName)

    def GetOutput(self, outputName) :
        if (outputName not in self.outputConnections) :
            return None
        deviceName,varName = self.outputConnections[outputName]
        return self.controller.Get(deviceName, varName)

    def SetOutput(self, outputName, value) :
        if (outputName not in self.outputConnections) :
            return None
        deviceName,varName = self.outputConnections[outputName]
        self.controller.Set(deviceName, varName, value)

    def Update(self) :
        pass

class Thermostat(Rule) :

    def GetInputNames(self) :
        return ['Temperature']

    def GetOutputNames(self) :
        return ['Heater', 'Chiller']

    def GetDefaultOptions(self) :
        return {'MinTemperature': 74,
                'MaxTemperature': 80}

    def Update(self) :
        temp = self.GetInput('Temperature')

        minTemp = self.GetOption('MinTemp')
        maxTemp = self.GetOption('MaxTemp')

        self.SetOutput('Heater', temp < minTemp)
        self.SetOutput('Chiller', temp > maxTemp)

class LightTimer(Rule) :
    
    def Init(self) :
        self.lastUpdateTime = datetime.time()

    def GetOutputNames(self) :
        return ['out']

    def GetDefaultOptions(self) :
        return {'OnTime': datetime.time(21,49,30),
                'OffTime': datetime.time(23)}
    
    def Run(self) :
        now = datetime.datetime.now().time()

        keys = ['OnTime','OffTime']
        values = {'OnTime': True, 'OffTime': False}
        
        # Sort the keys by time
        orderedKeys = sorted(keys, key=lambda x: self.GetOption(x))

        for key in orderedKeys :
            t = self.GetOption(key)
        
            if (self.lastUpdateTime < t and now >= t) :
                self.SetOutput('out', values[key])

        self.lastUpdateTime = now

class ToggleButtonRule(Rule) :

    def Init(self) :
        self.wasPressed = None

    def GetOutputNames(self) :
        return ['out']
    
    def GetInputNames(self) :
        return ['in']

    def Run(self) :
        isPressed = self.GetInput('in')

        # we use 'is False' here because we don't want the output
        # to be toggled when wasPressed has never been set
        if (isPressed and self.wasPressed is False) :
            val = not self.GetOutput('out')
            self.SetOutput('out', val)
        
        self.wasPressed = isPressed
