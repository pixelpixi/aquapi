import time, datetime, threading, glob

class Device(object) :

    Input = 'input'
    Output = 'output'
    Option = 'option'

    String = 'string'
    Int = 'int'
    Float = 'float'
    Bool = 'bool'

    def __init__(self) :
        self._variables = {}

    def Init(self) :
        pass

    def Update(self) :
        pass

    def GetVariables(self) :
        return self._variables

    def Get(self, key) :
        return self._variables[key]["value"]

    def Set(self, key, value) :
        var = self._variables[key];
        valueType = var['valueType']
        castValue = None
        if (valueType == self.String) :
            var['value'] = str(value)
        elif (valueType == self.Int) :
            var['value'] = int(value)
        elif (valueType == self.Float) :
            var['value'] = float(value)
        elif (valueType == self.Bool) :
            if (isinstance(value,basestring)) :
                var['value'] = value.lower() in ['1','true']
            else :
                var['value'] = bool(value)
        else :
            raise "Invalid value type"

    def CreateVariable(self, key, mode, valueType, defaultValue) :
        self._variables[key] = {
            'name': key,
            'mode': mode,
            'valueType': valueType,
            'value': defaultValue
            }

class TemperatureThread(threading.Thread) :

    def __init__(self, deviceFile) :
        threading.Thread.__init__(self)
        self.deviceFile = deviceFile
        self.tempF = None
        
    def run(self) :
        f = open(self.deviceFile, 'r')
        lines = f.readlines()
        f.close()

        print lines
        while lines[0].strip()[-3:] != 'YES':
            print 'Error reading temperature: ', lines
            return

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            self.tempC = float(temp_string) / 1000.0
            self.tempF = self.tempC * 9.0 / 5.0 + 32.0



class Temperature(Device) :
    def Init(self) :
        self.CreateVariable('Temperature', self.Input, self.Float, 78.0)

        self._deviceFile = deviceFolder = glob.glob('/sys/bus/w1/devices/28*/w1_slave')[0]
        self._lastRead = 0
        self._readInterval = 5
        self._thread = None

    def Update(self) :
        if (self._thread is not None and self._thread.isAlive()) :
            return

        if (self._thread and (self._thread.tempF is not None)) :
            self.Set('Temperature', self._thread.tempF)

        if (time.time() > self._lastRead+self._readInterval) :
            self._lastRead = time.time()
            self._thread = TemperatureThread(self._deviceFile)
            self._thread.start()

class VirtualTemperature(Device) :
    def Init(self) :
        self.CreateVariable('Temperature', self.Input, self.Float, 78.0)

class RelayBox(Device) :

    def Init(self) :
        import smbus
        self._bus = smbus.SMBus(0)

        self._names = [
            'Heater',
            'Return',
            'Carbon',
            'Skimmer',
            'Unused',
            'BioPellet',
            'SumpLight',
            'TopOff']
        defaultsOff = ['SumpLight', 'TopOff']
        
        self.CreateVariable('Address', self.Option, self.Int, 0x38)
        
        for name in self._names :
            self.CreateVariable(name, self.Output, self.Bool, name not in defaultsOff)

    def Update(self) :
        # Create an 8-bit value
        byte = 0
        for i in range(8) :
            outputName = self._names[i]
            if (not self.Get(outputName)) :
                byte = byte | (1 << i)
                
        # Write to the i2c bus
        address = self.Get('Address')
        self._bus.write_byte(address, byte)


class VirtualRelayBox(Device) :

    def Init(self) :
        self.CreateVariable('Address', self.Option, self.Int, 0x38)

        for i in range(8) :
            self.CreateVariable('Outlet%d' % i, self.Output, self.Bool, False)


class GPIORelayBox(Device) :

    def Init(self) :
        import RPi.GPIO as GPIO

        self._gpioPins = [7,8,9,10,22,23,24,25]
        self._values = [False]*8
        GPIO.setmode(GPIO.BCM)

        for i in range(8) :
            GPIO.setup(self._gpioPins[i], GPIO.OUT)
            GPIO.output(self._gpioPins[i], False)
            self.CreateVariable('Outlet%d' % i, self.Output, self.Bool, False)

    def Update(self) :
        import RPi.GPIO as GPIO

        for i in range(8) :
            outputName = 'Outlet%d' % i
            newValue = self.Get(outputName)
            if (newValue != self._values[i]) :
                self._values[i] = newValue
                GPIO.output(self._gpioPins[i], newValue)

class VirtualDevice(Device) :

    def Init(self) :
        self.CreateVariable('Incrementing', self.Option, self.Bool, False)

        self.CreateVariable('BoolOutput', self.Output, self.Bool, False)
        self.CreateVariable('IntOutput', self.Output, self.Int, 0)
        self.CreateVariable('FloatOutput', self.Output, self.Float, 0.0)
        self.CreateVariable('StringOutput', self.Output, self.String, "foo")

        self.CreateVariable('BoolInput', self.Input, self.Bool, False)
        self.CreateVariable('IntInput', self.Input, self.Int, 0)
        self.CreateVariable('FloatInput', self.Input, self.Float, 0.0)
        self.CreateVariable('StringInput', self.Input, self.String, "foo")

        self.CreateVariable('BoolOption', self.Option, self.Bool, False)
        self.CreateVariable('IntOption', self.Option, self.Int, 0)
        self.CreateVariable('FloatOption', self.Option, self.Float, 0.0)
        self.CreateVariable('StringOption', self.Option, self.String, "foo")

    def Update(self) :
        now = datetime.datetime.now()

        if (self.Get('Incrementing')) :
            self.Set('BoolInput', now.second % 2)        
            self.Set('FloatInput', now.second + now.microsecond/1e6)
            self.Set('IntInput', now.second)
            self.Set('StringInput', now.strftime("%A, %d. %B %Y %I:%M:%S%p"))

class IOExpansion(Device) :
    
    def Init(self) :
        import smbus
        self._bus = smbus.SMBus(0)
        
        self.CreateVariable('Address', self.Option, self.Int, 0x09)

        for i in range(6) :
            self.CreateVariable('Input%d' %i, self.Input, self.Bool, False)
    
    def Update(self) :
        address = self.Get('Address')
        inputByte = self._bus.read_byte(address)
        for i in range(6) :
            val = not bool(inputByte & (1 << i))
            self.Set('Input%d' % i, val)

class VirtualIOExpansion(Device) :
    def Init(self) :
        self.CreateVariable('Address', self.Option, self.Int, 0x09)

        for i in range(6) :
            self.CreateVariable('Input%d' %i, self.Input, self.Bool, False)

class AlternatingDevice(Device) :

    def Init(self) :
        self.CreateVariable('out', self.Input, self.Bool, False)

    def Update(self) :
        self.Set('out', int(time.time()/10) % 2)

        
