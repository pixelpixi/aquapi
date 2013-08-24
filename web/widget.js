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
	aquapy.BindValue(args['deviceName'], args['varName'], function(value) {
	    widget.content.html(value.toFixed(1) + "&deg;F");
	});
    } else {
	console.log('Invalid widget type: ' + args['type']);
    }
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
    var innerWidget = $('<div class="innerWidget">' +
	          '<table class="widgetTable">' +
                  '<tr><td class="widgetHeader">' + title + '</td><td class="widgetCloseIcon ">' +
                  '<img src="/images/gear-20.png"/>' +
		  '</td></tr>' +
		  '<tr><td colspan=2 class="widget"></td></tr></table>' +
		  '</div>');
    var settingsWidget = $('<div class="innerWidget">' +
	          '<table class="widgetTable">' +
                  '<tr><td class="widgetHeader"><input value="' + title + '">' +
	          '</input></td><td class="widgetCloseIcon ">' +
                  '<img src="/images/gear-20.png"/>' +
		  '</td></tr>' +
		  '<tr><td colspan=2 class="widget">Settings</td></tr>' +
	          '<tr><td colspan=2 class="widgetRemove">Remove</td></tr>' +
		  '</table></div>');
    var widget = this;
    
    outerWidget.append(innerWidget);
    outerWidget.append(settingsWidget);
    innerWidget.show();
    settingsWidget.hide();

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


    $('#widgetContainer').append(outerWidget);

    var titleElem = innerWidget.find('.widgetHeader');
    var titleInput = settingsWidget.find('.widgetHeader').find('input');

    var saveTitle = function() {
	title = titleInput.val();
	titleElem.text(title);
	saveWidgetsState();
    };
    titleInput.change(saveTitle);

    var showSettingsButton = innerWidget.find('.widgetCloseIcon')
    showSettingsButton.click(function() {
	settingsWidget.show();
	innerWidget.hide();
    });

    var hideSettingsButton = settingsWidget.find('.widgetCloseIcon')
    hideSettingsButton.click(function() {
	saveTitle();
	settingsWidget.hide();
	innerWidget.show();
    });

    var removeWidgetButton = settingsWidget.find('.widgetRemove');
    removeWidgetButton.click(function() {
	outerWidget.remove();
	allWidgets.splice(allWidgets.indexOf(widget), 1);
	saveWidgetsState();
    });	

    this.content = innerWidget.find('.widget');

    this.GetState = function() {
	return {
	    title: title,
	    left: outerWidget.position().left,
	    top: outerWidget.position().top,
	    width: outerWidget.width(),
	    height: outerWidget.height(),
	    creationArgs: args
	}
    }
    this.SetState = function(state) {
	title = state['title']
	titleElem.text(title);
	titleInput.val(title);
	outerWidget.css(state)
    }

    allWidgets.push(this);
    return this;
}
