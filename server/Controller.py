import Device, Rule
import time, traceback, os, json

class Controller(object) :

    ___instance = None

    def __init__(self) :
        if (self.___instance) :
            raise self.___instance
        self.___instance = self

        self.stateFilePath = '/home/ekt/aquapi.config'
        self.state = {}
        if (os.path.exists(self.stateFilePath)) :
            self.state = json.load(open(self.stateFilePath))

        self.devices = {
            'Temperature': Device.Temperature(),
            'RelayBox': Device.RelayBox(),
            'IO': Device.IOExpansion()
            }

        for device in self.devices.values() :
            device.Init()

        lightTimer = Rule.LightTimer(self)
        lightTimer.outputConnections['out'] = ('RelayBox','SumpLight')

        ato = Rule.ATO(self)
        ato.outputConnections['pump'] = ('RelayBox','TopOff')
        ato.inputConnections['level'] = ('IO', 'Input0')

        thermostat = Rule.Thermostat(self)
        thermostat.inputConnections['Temperature'] = ('Temperature', 'Temperature')
        thermostat.outputConnections['Heater'] = ('RelayBox', 'Heater')

        self.rules = [lightTimer, ato, thermostat]

        for rule in self.rules :
            rule.Init()

    def GetConfig(self) :
        config = {}
        for deviceName,device in self.devices.iteritems() :
            variables = {}
            for varName,var in device.GetVariables().iteritems() :
                variables[varName] = var
            device = {'variables': variables,
                      'name': deviceName}
            config[deviceName] = device
        return config

    def Set(self, deviceName, varName, value) :
        device = self.devices[deviceName]
        device.Set(varName, value)

    def Get(self, deviceName, varName) :
        device = self.devices[deviceName]
        return device.Get(varName)

    def SetState(self, key, value) :
        print 'Saving state file'
        self.state[key] = value
        json.dump(self.state, open(self.stateFilePath,'w'), indent=4)
        
    def GetState(self, key) :
        if (key in self.state) :
            return self.state[key]
        return None

    def Update(self) :
        for deviceName,device in self.devices.iteritems() :
            try :
                device.Update()
            except Exception, e:
                print 'Error updating device:', traceback.format_exc()
        for rule in self.rules :
            try :
                rule.Run()
            except Exception, e:
                print 'Error executing rule:', traceback.format_exc()

