import Device, Rule
import time, traceback

class Controller(object) :

    ___instance = None

    def __init__(self) :
        if (self.___instance) :
            raise self.___instance
        self.___instance = self

        self.devices = {
            'Temperature': Device.Temperature(),
            'RelayBox': Device.RelayBox(),
            'IO': Device.IOExpansion(),
            'Alternating': Device.AlternatingDevice(),
            'Virtual': Device.VirtualDevice()
            }

        for device in self.devices.values() :
            device.Init()

        lightTimer = Rule.LightTimer(self)
        toggleButton = Rule.ToggleButtonRule(self)

        lightTimer.outputConnections['out'] = ('RelayBox','Outlet0')
        toggleButton.outputConnections['out'] = ('RelayBox','Outlet0')
        toggleButton.inputConnections['in'] = ('IO','Input0')

        self.rules = [lightTimer, toggleButton]

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

