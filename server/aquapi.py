#!/usr/bin/python -B

import Device, Rule, Controller, Server

#relayBox = Device.RelayBox()
#io = Device.IOExpansion()

#relayBox.SetOutput('Outlet0', False)
#print io.GetInput('Input0')

#controller.Run()

import time, signal, sys

def _SignalHandler(signum, stack) :
    try :
        print 'Resetting GPIO'
        import RPi.GPIO as GPIO
        
        GPIO.cleanup()
    except ImportError:
        pass

    sys.exit(0)

signal.signal(signal.SIGINT, _SignalHandler)


controller = Controller.Controller()

Server.RunServer(controller)
