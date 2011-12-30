var TripApplication = function() {
    
    var Trip = Backbone.Model.extend({
        defaults: {
            "key": "new",
            "name": "New Trip",
            //"start_date": null,
            //"end_date": null,
            //"travelers": ["you"],
            "password": "travelisfun!"
        }
    });
    
    var TripList = Backbone.Collection.extend({
        model: Trip,
        url: "/trip"
    });
    
    var Trips = new TripList([
        {"name": "Hawaii"},
        {"name": "California"}
    ]);
    
    var AppView = Backbone.View.extend({
        el: $("body"),
        events: {
            "click #new-trip": "showPrompt"
        },
        showPrompt: function() {
            var trip_name = prompt("Name your trip!");
            Trips.add(new Trip({"name": trip_name}));
        }
    });
    
    var TripView = Backbone.View.extend({
        model: new Trip,
        tagName: "li",
        render: function() {
            $(this.el).html(this.model.get('name'));
            return this;
        }
    });
    
    var TripListView = Backbone.View.extend({
        el: $("#trip-list"),
        initialize: function() {
            var that = this;
            this._tripViews = [];
            this.collection.each(function(trip) {
                that._tripViews.push(new TripView({
                    model: trip
                }));
            });
        },
        render: function() {
            var that = this;
            $(this.el).empty();
            _(this._tripViews).each(function(dv) {
                $(that.el).append(dv.render().el);
            });
            return this;
        }
    });
    
    var appView = new AppView;
    var tripsView = new TripListView({
        collection: Trips
    });
    tripsView.render();
    
    // uncomment these for debugging
    //return {
    //    "Trip": Trip,
    //    "Trips": Trips,
    //    "appView": appView,
    //    "tripsView": tripsView
    //};
    
};
