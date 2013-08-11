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


class Socket(tornado.websocket.WebSocketHandler) :

    def open(self) :
        print 'Open'
        self.previousValues = {}
        self.timeout = None
        self._update()


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
    
    def _update(self) :

        for deviceName,device in self.application.controller.devices.iteritems() :
            for variableName,variable in device.GetVariables().iteritems() :
                newValue = self.application.controller.Get(deviceName, variableName)
                key = deviceName + '.' + variableName

                if (key not in self.previousValues or
                    self.previousValues[key] != newValue) :
                    self.previousValues[key] = newValue

                    data = {'deviceName': deviceName,
                            'varName': variableName,
                            'value': newValue}
                    print 'Sending valueChanged:',key,data
                    self.SendEvent('valueChanged',  data)

                                   
        ioloop = tornado.ioloop.IOLoop.instance()
        self.timeout = ioloop.add_timeout(ioloop.time() + .25, self._update)

def RunServer(controller) :

    application = tornado.web.Application([
            (r"/socket", Socket),
            (r"/", tornado.web.RedirectHandler, {"url": "/devices.html"}),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": "/home/ekt/AquaPi/web/"})
        ])

    application.controller = controller
    callback = tornado.ioloop.PeriodicCallback(controller.Update, 500)
    callback.start()

    application.listen(8888,'0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()

