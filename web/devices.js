
function loadDevices() {
    var contentContainer = $('.centeredContent');
    
    var outerTable = $('<table class="devicesTable"/>').appendTo(contentContainer);
    var outerTableRow = $('<tr/>').appendTo(outerTable);
    var deviceList = $('<td class="devicesList"/>').appendTo(outerTableRow);
    var deviceOptionsElem = $('<td class="deviceOptions">Test</td>').appendTo(outerTableRow);
    var config = {}

    var selectDevice = function(event) {
	$('.devicesList div').removeClass('selectedDeviceName');
	var selected = $(event.currentTarget);
	selected.addClass('selectedDeviceName');

	deviceOptionsElem.empty();
	var optionsTable = $('<table class="deviceOptionsTable"/>').appendTo(deviceOptionsElem);
	var deviceName = selected.text();
	var deviceOptions = config[deviceName];
	var varSpecs = deviceOptions['variables'];

	var modes = ['input','output','option'];
	var modeNames = ['Inputs','Outputs','Options'];
	for (var modeIndex in modes) {
	    var mode = modes[modeIndex];
	    $('<tr><td class="deviceOptionsHeader" colspan=2>' + 
	      modeNames[modeIndex] + '</td></tr>').appendTo(optionsTable);
	    for (var variableName in varSpecs) {
    		var variable = varSpecs[variableName];
		if (variable['mode'] != mode) {
		    continue;
		}
		console.log(variable['mode'] + ":" + mode);
		var row = $('<tr/>').appendTo(optionsTable);
		var varDiv = $('<div/>').appendTo(deviceOptionsElem);
		$('<td class="variableTableNames">' + variableName + '</td>').appendTo(row);
		var controlElem = $('<td/>').appendTo(row);
		createVarWidget(deviceName, variable).appendTo(controlElem);
	    }
	}

	console.log($(event.currentTarget).text())
    }


    function loadConfig(newConfig) {
	config = newConfig;
	for (var deviceName in config) {
	    var deviceNameDiv = $('<div class="deviceName">' + deviceName + '</div>').appendTo(deviceList);
	    deviceNameDiv.click(selectDevice);
	}
    }

    aquapy.Bind('config', loadConfig);
    aquapy.Bind('open', function() {
	aquapy.Send('getConfig', {});
    });
}