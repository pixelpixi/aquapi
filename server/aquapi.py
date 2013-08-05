#!/usr/bin/python -B

import Device, Rule, Controller, Server

#relayBox = Device.RelayBox()
#io = Device.IOExpansion()

#relayBox.SetOutput('Outlet0', False)
#print io.GetInput('Input0')

#controller.Run()

import RPi.GPIO as GPIO
import time, signal, sys

def _SignalHandler(signum, stack) :
    print 'Resetting GPIO'
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, _SignalHandler)


controller = Controller.Controller()

Server.RunServer(controller)
