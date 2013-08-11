"use strict";

var allWidgets = new Array();

function saveWidgetsState() {
    var widgetState = [];
    for (var i=0; i < allWidgets.length; i++) {
	widgetState.push(allWidgets[i].GetState());
    }
    aquapy.SaveState('statusWidgets', widgetState);
}

function loadWidgetState() {
    var loadStateCB = function (data) {
	console.log(data);
	var widgetsByTitle = {}
	for (var i=0; i < allWidgets.length; i++) {
	    var state = allWidgets[i].GetState();
	    widgetsByTitle[state.title] = allWidgets[i];
	}

	for (var i=0; i < data.length; i++) {
	    var widget = widgetsByTitle[data[i].title];
	    if (widget == undefined) {
		widget = manufactureWidget(data[i].creationArgs);
	    }
	    widget.SetState(data[i]);
	}
    }

    aquapy.LoadState('statusWidgets', loadStateCB);
}

function manufactureWidget(args) {
    var widget = new Widget(args);
    
    if (args['type'] == 'toggle') {
	var button = createButton(args['deviceName'], {'name': args['varName']});
	widget.content.append(button);
    }
    else if (args['type'] == 'cell') {
	widget.content.addClass('temperature');
	var v = new Variable(
	    args['deviceName'],args['varName'],
	    function (value) { 
		widget.content.html(value.toFixed(1) + "&deg;F");
	    });
    } else {
	console.log('Invalid widget type: ' + args['type']);
    }
    return widget;
}

function makeTemperatureWidget(title, deviceName, varName) {
    var widget = new Widget(title);
    widget.content.addClass('temperature');
    var v = new Variable(
	deviceName,varName,
	function (value) { 
	    widget.content.text(value.toFixed(1) + "&deg;F");
	});
}

function makeButtonWidget(title, deviceName, varName) {
    var widget = new Widget(title);
    var button = createButton(deviceName,{'name': varName});
    widget.content.append(button);
    return widget;
}

function showCreateWidgetDialog() {
    var dialog = $('<div></div>');
    var ok = function() {
	var args = {};
	var splitName = variableSelector.val().split(':');
	args['deviceName'] = splitName[0];
	args['varName'] = splitName[1];
	args['title'] = title.val();
	args['type'] = widgetType.val();

	manufactureWidget(args);
	dialog.dialog('close');
    }
    
    dialog.dialog({'title': 'Add Widget',
		   'buttons': [{text: 'Ok', click: ok}]
		  });

    var widgetType = $('<select>').appendTo(dialog);
    $('<option value="toggle">Toggle Button</option>').appendTo(widgetType);
    $('<option value="cell">Value Cell</option>').appendTo(widgetType);
    
    var title = $('<input/>').appendTo(dialog);

    var variableSelector = $('<select/>').appendTo(dialog);

    aquapy.Bind('config', function (config) {
	console.log(config);
	for (var deviceName in config) {
	    var device = config[deviceName];
	    var variables = device['variables'];
	    for (var variableName in variables) {
		var variable = variables[variableName];
		var key = deviceName + ":" + variableName;
		$('<option value="' + key + '">' + key + '</option>').appendTo(variableSelector);
	    }
	    
	}
    });
    aquapy.Send('getConfig', {});
    
    widgetType.menu();

    return dialog;
}

function Widget(args) {
    var title = args['title'];
    var outerWidget = $('<div class="outerWidget"/>');
    var table = $('<div class="innerWidget">' +
	          '<table class="widgetTable">' +
                  '<tr><td class="widgetTitle">' + title +
		  '</td></tr>' +
		  '<tr><td class="widget"></td></tr></table>' +
		  '</div>');
    var widget = this;

    
    outerWidget.append(table);

    outerWidget.draggable({
        stack: "#widgetContainer div",
        containment: "parent",
        stop: function(e, ui) {
            var elem = ui.helper,
                left = elem.position().left,
                top  = elem.position().top;

            elem.css({
                left: Math.round(left/100)*100,
                top: Math.round(top/100)*100
            });
            saveWidgetsState();
        }
    });
    outerWidget.resizable({
	grid: 100,
	containment: "parent",
	stop: function (e, ui) {
	    saveWidgetsState();
	}
    });
    outerWidget.css({position:"absolute"});

    outerWidget.width(100);
    outerWidget.height(100);

    var closeButton = $('<span class="widgetCloseButton">X</span>');
    outerWidget.append(closeButton);
    $('#widgetContainer').append(outerWidget);
    closeButton.click(function() {
	allWidgets.splice(allWidgets.indexOf(widget), 1);
	console.log(allWidgets);
	outerWidget.remove();
	saveWidgetsState();
    });

    this.content = outerWidget.find('.widget');

    this.GetState = function() {
	return {
	    title: outerWidget.find('.widgetTitle').text(),
	    left: outerWidget.position().left,
	    top: outerWidget.position().top,
	    width: outerWidget.width(),
	    height: outerWidget.height(),
	    creationArgs: args
	}
    }
    this.SetState = function(state) {
	outerWidget.find('.widgetTitle').text(state['title']);
	outerWidget.css(state)
    }

    allWidgets.push(this);
    return this;
}
