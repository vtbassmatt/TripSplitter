var TripApplication = function() {
    
    var Trip = Backbone.Model.extend({
        promptColor: function() {
            var cssColor = prompt("Enter a CSS color");
            this.set({color: cssColor});
        }
    });
    
    window.trip = new Trip;
    
    trip.bind('change:color', function(model, color) {
        $('#trip').css({background: color});
    });
    
    trip.set({color: 'white'});
    
    trip.promptColor();
    
};
