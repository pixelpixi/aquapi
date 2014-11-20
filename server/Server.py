#!/usr/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.web

import os, json, math, base64


class Template(tornado.web.RequestHandler) :

    @tornado.web.authenticated
    def get(self) :
        self.write(open(os.path.join(self.application.baseDir,'web/aquapi.html')).read())

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        print 'User is: ', user
        return user

class Login(tornado.web.RequestHandler) :

    password = 'fugu'

    def get(self) :
        self.write(open(os.path.join(self.application.baseDir,'web/aquapi.html')).read())

    def post(self) :
        print "'%s'" % self.get_argument("pwd")
        if (self.get_argument("pwd") == self.password) :
            self.set_secure_cookie("user", "aquapi")
            self.redirect(self.get_argument('next', '/'))
        else :
            self.set_secure_cookie("user", None)

    def get_current_user(self):
        return self.get_secure_cookie("user")

class Logout(tornado.web.RequestHandler) :

    def get(self) :
        self.clear_cookie('user')
        self.redirect("/login")

class Socket(tornado.websocket.WebSocketHandler) :

    def open(self) :
        self.timeout = None
        self._deviceDescriptions = {}
        self._varValues = {}
        self._varDescriptions = {}

        if (not self.get_secure_cookie("user")) :
            print 'Closing websocket. Not authenticated'
            self.close()
            return

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


def GetCookieSecret() :
    secretfile = '/home/ekt/aquapi.secret'
    if (os.path.exists(secretfile)) :
        secret = open(secretfile).read().strip()
    else :
        secret = base64.b64encode(os.urandom(32))
        open(secretfile,'w').write(secret + "\n")
    # XXX: Is it secure to return this in a base64 encoded form?
    return secret

def RunServer(controller) :
    baseDir = os.path.dirname(os.path.dirname(__file__))
    print baseDir

    cookieSecret = GetCookieSecret()

    handlers = [
        (r"/socket", Socket),
        (r"/", Template),
        (r"/login", Login),
        (r"/logout", Logout),
        (r"/devices", Template),
        (r"/rules", Template),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(baseDir,'web')})
        ]
    
    application = tornado.web.Application(
        handlers,
        login_url = "/login",
        cookie_secret =  cookieSecret
        )

    application.controller = controller
    application.baseDir = baseDir
    callback = tornado.ioloop.PeriodicCallback(controller.Update, 500)
    callback.start()

    application.listen(80, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()

