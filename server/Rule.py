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
        return {'MinTemp': 74,
                'MaxTemp': 80}

    def Run(self) :
        temp = self.GetInput('Temperature')

        minTemp = self.GetOption('MinTemp')
        maxTemp = self.GetOption('MaxTemp')

        self.SetOutput('Heater', temp < minTemp)
        self.SetOutput('Chiller', temp > maxTemp)

class ATO(Rule) :
    def Init(self) :
        pass

    def GetOutputNames(self) :
        return ['pump']

    def GetInputNames(self) :
        return ['level']

    def Run(self) :
        # Limit ATO to 15 minutes twice a day
        now = datetime.datetime.now()
        if ((now.hour != 8 and now.hour != 20) or
            now.minute > 15) :
            self.SetOutput('pump', False)
            return

        self.SetOutput('pump', self.GetInput('level'))
    

class LightTimer(Rule) :
    
    def Init(self) :
        self.lastUpdate = datetime.datetime.now()-datetime.timedelta(days=1)

    def GetOutputNames(self) :
        return ['out']

    def GetDefaultOptions(self) :
        return {'OnTime': datetime.time(18,00,00),
                'OffTime': datetime.time(0,00,00)}
    
    def Run(self) :
        now = datetime.datetime.now()

        keys = ['OnTime', 'OffTime']
        values = {'OnTime': True, 'OffTime': False}
        
        # Sort the keys by time
        orderedKeys = sorted(keys, key=lambda x: self.GetOption(x))

        newValue = None
        for dayOffset in [-1, 0] :
            for key in orderedKeys :
                t = datetime.datetime.combine(now.date(), self.GetOption(key))
                t = t+datetime.timedelta(days=dayOffset)
                if (self.lastUpdate < t and now >= t) :
                    newValue = values[key]
                    self.lastUpdate = t

        self.lastUpdate = now
        if (newValue is not None) :
            self.SetOutput('out', newValue)

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
