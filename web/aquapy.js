"use strict";

function AquaPy() {
    var _socket;
    var aquapy = this;
    var currentURL = undefined;

    // Connection
    this.Connect = function(url) {
	currentURL = url;
	_socket = new WebSocket(url);
	_socket.onmessage = function(evt) {
	    var payload = JSON.parse(evt.data);
	    if (payload['event'] == undefined || payload['data'] == undefined) {
		console.log('Received invalid message: ' + evt.data);
		return;
	    }

            dispatch(payload['event'], payload['data']);
	};
	_socket.onclose = function(){
	    console.log('Close');
	    dispatch('close', null)
	    aquapy.ShowConnectDialog();
	}
	_socket.onopen = function(){
	    console.log('Open');
	    dispatch('open', null)
	}
    }

    //
    // State
    //


    this.SaveState = function(key, value) {
	this.Send('saveState', {
	    key: key,
	    value: value});
    }

    this.LoadState = function(key, callback) {
	this.Bind('loadState', function (data) {
	    if (data['key'] == key) {
		callback(data['value'])
	    }
	});

	this.Send('loadState', key);
    }

    //
    // Show connect dialog
    //
    this.ShowConnectDialog = function() {
	var dialog = $('<div>The connection to the server has been lost.</div>').dialog({
	    dialogClass: 'no-close',
	    modal: true,
	    title: 'Connection Lost',
	    buttons: {"Reconnect": function () {
		console.log('Reconnect');
		$(this).dialog('close');
		aquapy.Connect(currentURL);
	    }}})
    }

    

    //
    // Event Binding Utilities
    //

    var _callbacks = {};

    // Register a callback when an event with the given
    // eventName is received.
    this.Bind = function(eventName, callback) {
	_callbacks[eventName] = _callbacks[eventName] || [];
	_callbacks[eventName].push(callback);
    };

    // Send an event to the server
    this.Send = function(eventName, eventData){
	var payload = JSON.stringify({'event':eventName, 'data': eventData});
	_socket.send(payload);
    };
    
    var dispatch = function(eventName,  data){
	var chain = _callbacks[eventName];
	if (typeof chain == 'undefined') return; // no callbacks for this event
	for(var i = 0; i < chain.length; i++){
	    chain[i]( data )
	}
    };

    //
    // Devices
    //
    var devices = {}

    var onDeviceChanged = function(data) {
	devices[data['deviceName']] = data;
    }
    var onDeviceRemoved = function(data) {
	var index = devices.indexOf[data['deviceName']];
	if (index >= 0) {
	    devices.splice(index,1);
	}
    }
    this.GetDevices = function() {
	return devices;
    }
    this.Bind('deviceChanged', onDeviceChanged);
    this.Bind('deviceRemoved', onDeviceRemoved);

    //
    // Variables
    //
    
    var variables = {}

    var onVariableChanged = function(data) {
	devices[data['varName']] = data;
    }
    var onVariableRemoved = function(data) {
	var index = devices.indexOf[data['varName']];
	if (index >= 0) {
	    devices.splice(index,1);
	}
    }
    
    // Get the the configuration dictionary for a particular variable
    this.GetVariable = function(deviceName, varName) {
	return variables[deviceName + ":" + varName];
    }

    this.Bind('variableChanged', onVariableChanged);
    this.Bind('variableRemoved', onVariableRemoved);

    //
    // Values
    //

    var values = {}

    // Get the value for a particular variable
    this.GetValue = function(deviceName, varName) {
	return values[deviceName + ":" + varName];
    }
    this.SetValue = function(deviceName, varName, value) {
	this.Send('setValue', {'deviceName': deviceName, 'varName': varName, 'value': value})
    }
    
    var _valueCallbacks = {};
    this.BindValue = function(deviceName, varName, callback) {
	var key = deviceName + ":" + varName;
	_valueCallbacks[key] = _valueCallbacks[key] || [];
	_valueCallbacks[key].push(callback);

	// If we already have a value for this key, them immediately
	// call the callback.
	if (typeof values[key] != undefined) {
	    callback(values[key]);
	}
    }

    var onValueChanged = function(data) {
	var key = data['deviceName'] + ':' + data['varName']

	// Store the value locally
	values[key] = data['value']

	var chain = _valueCallbacks[key];
	if (typeof chain == 'undefined') {
	    return;
	}
	for (var i=0; i < chain.length; i++) {
	    chain[i](data['value']);
	}
    }

    this.Bind('valueChanged', onValueChanged);
};

function createReadOnlyButton(deviceName, varInfo) {
    var div = $('<div class="readOnlyButton ui-state-default">Off</div>');
    var varName = varInfo['name'];

    var setChecked = function(checked) {
	if (checked) {
	    div.removeClass('ui-state-default');
	    div.addClass('ui-state-active');
	    div.text('On');
	} else {
	    div.addClass('ui-state-default');
	    div.removeClass('ui-state-active');
	    div.text('Off');
	}
	div.change();
    }

    aquapy.BindValue(deviceName, varName, setChecked);

    return div;
}

function createButton(deviceName, varInfo, readOnly) {
    var varName = varInfo['name']

    var div = $('<span/>');
    var checkbox = $('<input type="checkbox"/>').uniqueId().appendTo(div);
    var label = $('<label for="' + checkbox.attr('id') + '">On</label>').appendTo(div);
    checkbox.button();

    var setChecked = function(checked) {
	checkbox.button('option','label',checked ? 'On' : 'Off');
	checkbox.prop('checked', checked);
	checkbox.button('refresh');
    };

    if (readOnly) {
	label.click(function(event) {
	    event.preventDefault();
	    event.stopPropagation();
	})
	label.hover(function(event) {
	    event.preventDefault();
	    event.stopPropagation();
	})
    }

    checkbox.click(function(event) {
	console.log('Click');
	var checked = checkbox.is(':checked');
	aquapy.SetValue(deviceName, varName, checked)
    });

    aquapy.BindValue(deviceName, varName, setChecked);
    return div;
}


function createTextInput(deviceName, varInfo) {
    var textbox = $('<input />', { type: 'text'});

    console.log(varInfo);
    textbox.val(varInfo['value']);
    textbox.change(function(data) {
	console.log('changed: ' + data);
	var varName = varInfo['name'];
	aquapy.SetValue(deviceName, varName, textbox.val())
    })

    var cb = function(data) {
	if (data['deviceName'] != deviceName ||
	    data['varName'] != varInfo['name']) {
	    return;
	}

	var value = data['value'];
	textbox.val(value);
    };
    aquapy.Bind('valueChanged', cb);
    return textbox;
}

function createValueCell(deviceName, varInfo) {
    var div = $('<span class="valueCell"></span>');
    div.html(varInfo['value']);
    var cb = function(data) {
	if (data['deviceName'] != deviceName ||
	    data['varName'] != varInfo['name']) {
	    return;
	}
	div.text(data['value'].toFixed(1));
    };
    aquapy.Bind('valueChanged', cb);
    return div;
}


function createVarWidget(deviceName, varInfo) {
    switch (varInfo['valueType']) {    
    case 'bool':
	if (varInfo['mode'] == 'input') {
	    return createReadOnlyButton(deviceName, varInfo);
	} else {
            return createButton(deviceName, varInfo);
	}
    case 'float':
    case 'int':
    case 'string':
	console.log(varInfo);
	if (varInfo['mode'] == 'input') {
            return createValueCell(deviceName, varInfo);
        } else {
            return createTextInput(deviceName, varInfo);
	}
    default :
        console.log('Error: Cannot create widget for type ' + varInfo['valueType']);
    }
}
