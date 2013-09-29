#!/usr/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import json, math

import tornado.ioloop
import tornado.web

import os

class ToggleHandler(tornado.web.RequestHandler) :
    def initialize(self) :
        self.controller = self.application.controller

    def get(self) :
        deviceName = self.get_argument('deviceName')
        varName = self.get_argument('varName')
        value = self.controller.Get(deviceName, varName)
        print 'Toggle', value
        self.controller.Set(deviceName, varName, not value)

class SetValue(tornado.web.RequestHandler) :
    def initialize(self) :
        self.controller = self.application.controller

    def get(self) :
        controller = self.application.controller
        deviceName = self.get_argument('deviceName')
        varName = self.get_argument('varName')
        value = self.get_argument('value')
        print 'Set', deviceName, varName, value
        self.controller.Set(deviceName, varName, value)

class GetConfig(tornado.web.RequestHandler) :

    def get(self) :
        print 'Get Config'
        self.write(json.dumps(vars))


class Template(tornado.web.RequestHandler) :
    def get(self) :
        self.write(open(os.path.join(self.application.baseDir,'web/aquapi.html')).read())

class Socket(tornado.websocket.WebSocketHandler) :

    def open(self) :
        print 'Open'
        self._deviceDescriptions = {}
        self._varValues = {}
        self._varDescriptions = {}

        self.timeout = None
        self._Update()
        self.SendEvent('loaded',{})


    def HandleEvent(self, event, data) :
        if (event == 'getConfig') :
            config = self.application.controller.GetConfig()
            self.SendEvent('config', config)
        elif (event == 'setValue') :
            self.application.controller.Set(data['deviceName'],
                                            data['varName'],
                                            data['value'])
        elif (event == 'saveState') :
            self.application.controller.SetState(
                data['key'], data['value'])
        elif (event == 'loadState') :
            state = self.application.controller.GetState(data);
            self.SendEvent('loadState',
                {'key': data, 'value': state});
        else :
            print 'Error: Received invalid event: ', event;

    def SendEvent(self, event, data) :
        payload = {'event': event, 'data': data}
        self.write_message(json.dumps(payload))
            
    def on_message(self, message) :
        payload = json.loads(message)
        event = payload['event']
        data = payload['data']
        if (event == None) :
            print('Received invalid message from client: ' + message);
        else :
            self.HandleEvent(event, data)

    def on_close(self) :
        ioloop = tornado.ioloop.IOLoop.instance()
        if (self.timeout) :
            ioloop.remove_timeout(self.timeout)
    
    def _Update(self) :

        for deviceName,device in self.application.controller.devices.iteritems() :
            self._UpdateDeviceDescription(deviceName, device)

            for variableName,variable in device.GetVariables().iteritems() :
                self._UpdateVarDescription(deviceName, variableName, variable)
                self._UpdateVarValue(deviceName, variableName, device.Get(variableName))

                                   
        ioloop = tornado.ioloop.IOLoop.instance()
        self.timeout = ioloop.add_timeout(ioloop.time() + .25, self._Update)

    def _UpdateDeviceDescription(self, deviceName, device) :
        deviceDescription = {'deviceName': deviceName,
                                 'variables': device.GetVariables().keys()}
        if (deviceName not in self._deviceDescriptions or
            self._deviceDescriptions[deviceName] != deviceDescription) :
            self._deviceDescriptions[deviceName] = deviceDescription
            self.SendEvent('deviceChanged', deviceDescription)

    def _UpdateVarDescription(self, deviceName, varName, variable) :
        # Key that uniquely identifies this variable
        key = deviceName + ':' + varName

        # The variable description is just the mode right now, but this
        # will be expanded in the future.
        varDescription = {
            'deviceName': deviceName,
            'varName': varName,
            'mode':  variable["mode"]}
        if (key not in self._varDescriptions or
            self._varDescriptions[key] != varDescription) :
            self._varDescriptions[key] = varDescription
            self.SendEvent('variableChanged', varDescription)
    
    def _UpdateVarValue(self, deviceName, varName, value) :
        # Key that uniquely identifies this variable
        key = deviceName + ':' + varName

        varValue = {'deviceName': deviceName,
                    'varName': varName,
                    'value': value}
        if (key not in self._varValues or
            self._varValues[key] != varValue) :
            self._varValues[key] = varValue
            self.SendEvent('valueChanged',  varValue)


def RunServer(controller) :
    baseDir = os.path.dirname(os.path.dirname(__file__))
    print baseDir

    application = tornado.web.Application([
            (r"/socket", Socket),
            (r"/", Template),
            (r"/devices", Template),
            (r"/rules", Template),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(baseDir,'web')})
        ])

    application.controller = controller
    application.baseDir = baseDir
    callback = tornado.ioloop.PeriodicCallback(controller.Update, 500)
    callback.start()

    application.listen(8888,'0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()

