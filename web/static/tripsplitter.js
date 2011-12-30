window.Trip = Backbone.Model.extend();

window.TripCollection = Backbone.Collection.extend({
    model: Trip,
    url: '/api/trip'
});

window.TripListView = Backbone.View.extend({
    el: $('#tripList'),
    initialize: function() {
        console.log('TripListView::initialize');
        this.model.bind('reset', this.render, this);
    },
    render: function(eventName) {
        console.log('TripListView::render');
        _.each(this.model.models, function(trip) {
            $(this.el).append(new TripListItemView({model: trip}).render().el);
        }, this);
        return this;
    }
});

window.TripListItemView = Backbone.View.extend({
    tagName: "li",
    template: _.template($('#trip-list-item').html()),
    render: function(eventName) {
        console.log('TripListItemView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

window.TripView = Backbone.View.extend({
    el: $('#mainArea'),
    template: _.template($('#trip-details').html()),
    render: function(eventName) {
        console.log('TripView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

var AppRouter = Backbone.Router.extend({
    routes: {
        ""              : "list",
        "trips/:id"      : "tripDetails"
    },
    
    list: function() {
        console.log('list');
        this.tripList = new TripCollection();
        this.tripListView = new TripListView({model: this.tripList});
        this.tripList.fetch();
    },
    
    tripDetails: function(id) {
        console.log('tripDetails(' + id + ')');
        this.trip = this.tripList.get(id);
        this.tripView = new TripView({model: this.trip});
        this.tripView.render();
    }
});

var app = new AppRouter();
Backbone.history.start();

