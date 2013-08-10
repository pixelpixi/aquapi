"use strict";

function makeWidget() {
    var outerWidget = $('<div class="outerWidget"/>');
    var widget = $('<div class="widget"/>').appendTo(outerWidget);

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
        }
    });
    outerWidget.resizable({
	grid: 100,
	containment: "parent"
    });
    outerWidget.css({position:"absolute"});

    outerWidget.width(100);
    outerWidget.height(100);
    
    $('#widgetContainer').append(outerWidget);
    return widget;
}

