window.Trip = Backbone.Model.extend({
    urlRoot: "/api/trip",
    defaults: {
        "id": null,
        "name": "",
        "password": ""
    }
    // TODO: override toJSON so that only certain attributes will
    //       be sent up
});

window.TripCollection = Backbone.Collection.extend({
    model: Trip,
    url: '/api/trip'
});

window.TripListView = Backbone.View.extend({
    el: $('#tripList'),
    initialize: function() {
        console.log('TripListView::initialize');
        this.model.bind('reset', this.render, this);
        this.model.bind('add', function(trip) {
            $('#tripList').append(
                new TripListItemView({model: trip}).render().el);
        });
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
    
    initialize: function() {
        console.log('TripListItemView::initialize');
        this.model.bind("change", this.render, this);
        this.model.bind("destroy", this.close, this);
    },
    
    render: function(eventName) {
        console.log('TripListItemView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    },
    
    close: function() {
        console.log('TripListItemView::close');
        $(this.el).unbind();
        $(this.el).remove();
    }
});

window.TripView = Backbone.View.extend({
    el: $('#mainArea'),
    
    template: _.template($('#trip-details').html()),
    
    initialize: function() {
        console.log('TripView::initialize');
        this.model.bind("change", this.render, this);
    },
    
    render: function(eventName) {
        console.log('TripView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    },
    
    events: {
        "change input": "change",
        "click .save": "saveTrip",
        "click .delete": "deleteTrip"
    },
    
    change: function(event) {
        console.log('TripView::change');
        var target = event.target;
        console.log('changing ' + target.id + ' from "'
            + target.defaultValue + '" to "' + target.value + '"');
        // could change model on the spot here
        // var change = {};
        // change[target.name] = target.value;
        // this.model.set(change);
    },
    
    saveTrip: function() {
        console.log('TripView::saveTrip');
        this.model.set({
            name: $('#name').val(),
            password: $('#password').val()
        });
        if (this.model.isNew()) {
            console.log("the model is new");
            var self = this;
            app.tripList.create(this.model, {
                'success' : function() {
                    // update the URL without actually navigating
                    app.navigate('trips/'+self.model.id, false);
                },
                'error'   : function(model, response){
                    errStr = "Error " +response.status +
                    ": " + response.responseText;
                    alert(errStr);
                }
            });
        } else {
            console.log("the model is not new");
            this.model.save();
        }
        return false;
    },
    
    deleteTrip: function() {
        console.log('TripView::deleteTrip');
        this.model.destroy({
            success: function() {
                alert('Trip deleted');
                window.history.back();
            }
        });
        return false;
    },
    
    close: function() {
        console.log('TripView::close');
        $(this.el).unbind();
        $(this.el).empty();
    }
});

window.HeaderView = Backbone.View.extend({
    el: $('.header'),
    
    template: _.template($('#header').html()),
    
    initialize: function() {
        console.log('HeaderView::initialize');
        $(this.el).html(this.template());
        return this;
    },
    
    events: {
        "click .new": "newTrip"
    },
    
    newTrip: function(event) {
        console.log('HeaderView::newTrip');
        if(app.tripView) app.tripView.close();
        app.tripView = new TripView({model: new Trip()});
        app.tripView.render();
        return false;
    }
});

var AppRouter = Backbone.Router.extend({
    routes: {
        ""              : "list",
        "trips/:id"     : "tripDetails"
    },
    
    list: function() {
        console.log('list');
        this.tripList = new TripCollection();
        var self = this;
        this.tripList.fetch({
            success: function() {
                console.log('list$success');
                self.tripListView = new TripListView({model: self.tripList});
                self.tripListView.render();
                if(self.requestedId) self.tripDetails(self.requestedId);
            }
        });
    },
    
    tripDetails: function(id) {
        console.log('tripDetails(' + id + ')');
        if(this.tripList) {
            console.log('found tripList');
            this.trip = this.tripList.get(id);
            if(app.tripView) app.tripView.close();
            this.tripView = new TripView({model: this.trip});
            this.tripView.render();
        } else {
            console.log('did not find tripList');
            this.requestedId = id;
            this.list();
        }
    }
});

var app = new AppRouter();
Backbone.history.start();
var header = new HeaderView();
