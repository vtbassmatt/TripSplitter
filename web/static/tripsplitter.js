// usage: log('inside coolFunc',this,arguments);
// http://paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console){
    console.log( Array.prototype.slice.call(arguments) );
  }
};

// extend date to handle the dates which come down from the server
Date.prototype.fromJSON = function(json_obj) {
    if(json_obj.year)  this.setYear(json_obj.year);
    // fun fact: JS months count from 0
    if(json_obj.month) this.setMonth(json_obj.month - 1);
    if(json_obj.day)   this.setDate(json_obj.day);
};

// and a "class" method for building dates from JSON directly
Date.fromJSON = function(json_obj) {
    d = new Date();
    d.fromJSON(json_obj);
    return d;
};

window.Trip = Backbone.Model.extend({
    urlRoot: "/api/trip",
    defaults: {
        "id": null,
        "name": "",
        "password": "",
        "start_date": (new Date()).toDateString(),
        "end_date": (new Date()).toDateString(),
        "travelers": []
    },
    parse: function(response) {
        log('Trip::parse');
        dates = ["create_date", "end_date", "modify_date", "start_date"];
        for(i in dates) {
            var date = dates[i];
            if(response[date]) {
                response[date] = (Date.fromJSON(response[date])).toDateString();
            }
        }
        return response;
    },
    initialize: function() {
        log('Trip::initialize');
        this.expenses = new ExpenseCollection();
        var self = this;
        this.expenses.url = function() { 
            if(self.id) return '/api/trip/' + self.id + '/expenses';
            throw "Trip must be fetched or saved before expenses URL is valid";
        }
    }
    // TODO: override toJSON so that only certain attributes will
    //       be sent up
});

window.Expense = Backbone.Model.extend({
    defaults: {
        "id": null,
        "description": "",
        "creator": "",
        "expense_date": (new Date()).toDateString(),
        "travelers": [],
        "value": 0,
        "currency": ""
    },
    parse: function(response) {
        log('Expense::parse');
        dates = ["create_date", "expense_date", "modify_date"];
        for(i in dates) {
            var date = dates[i];
            if(response[date]) {
                response[date] = (Date.fromJSON(response[date])).toDateString();
            }
        }
        return response;
    }
});

window.TripCollection = Backbone.Collection.extend({
    model: Trip,
    url: '/api/trip',
    parse: function(response) {
        log('TripCollection::parse');
        for(i in response) {
            Trip.prototype.parse(response[i]);
        }
        return response;
    }
});

window.ExpenseCollection = Backbone.Collection.extend({
    model: Expense,
    initialize: function(models, args) {
        log('ExpenseCollection::initialize');
    },
    // URL must be set by the instantiator
    parse: function(response) {
        log('ExpenseCollection::parse');
        for(i in response) {
            Expense.prototype.parse(response[i]);
        }
        return response;
    }
});

window.TripListView = Backbone.View.extend({
    el: $('#tripList'),
    initialize: function() {
        log('TripListView::initialize');
        $(this.el).empty();
        this.model.bind('reset', this.render, this);
        this.model.bind('add', function(trip) {
            $('#tripList').append(
                new TripListItemView({model: trip}).render().el);
        });
    },
    render: function(eventName) {
        log('TripListView::render');
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
        log('TripListItemView::initialize');
        this.model.bind("change", this.render, this);
        this.model.bind("destroy", this.close, this);
    },
    
    render: function(eventName) {
        log('TripListItemView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    },
    
    close: function() {
        log('TripListItemView::close');
        $(this.el).unbind();
        $(this.el).remove();
    }
});

window.TripView = Backbone.View.extend({
    el: $('#mainArea'),
    
    template: _.template($('#trip-details').html()),
    
    initialize: function() {
        log('TripView::initialize');
        this.model.bind("change", this.render, this);
    },
    
    render: function(eventName) {
        log('TripView::render');
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    },
    
    events: {
        "change input": "change",
        "click .save": "saveTrip",
        "click .delete": "deleteTrip"
    },
    
    change: function(event) {
        log('TripView::change');
        var target = event.target;
        log('changing ' + target.id + ' from "'
            + target.defaultValue + '" to "' + target.value + '"');
        // could change model on the spot here
        // var change = {};
        // change[target.name] = target.value;
        // this.model.set(change);
    },
    
    saveTrip: function() {
        log('TripView::saveTrip');
        this.model.set({
            name: $('#name').val(),
            password: $('#password').val(),
            start_date: $('#start_date').val(),
            end_date: $('#end_date').val(),
            travelers: $('#travelers').val().split(",")
        });
        if (this.model.isNew()) {
            log("the model is new");
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
            log("the model is not new");
            this.model.save();
        }
        return false;
    },
    
    deleteTrip: function() {
        log('TripView::deleteTrip');
        var self = this;
        this.model.destroy({
            success: function() {
                self.close();
                alert('Trip deleted');
                window.history.back();
            }
        });
        return false;
    },
    
    close: function() {
        log('TripView::close');
        $(this.el).unbind();
        $(this.el).empty();
    }
});

window.HeaderView = Backbone.View.extend({
    el: $('.header'),
    
    template: _.template($('#header').html()),
    
    initialize: function() {
        log('HeaderView::initialize');
        $(this.el).html(this.template());
        return this;
    },
    
    events: {
        "click .new": "newTrip",
        "click .home": "home"
    },
    
    newTrip: function(event) {
        log('HeaderView::newTrip');
        app.navigate("trips/new", true);
        return false;
    },
    
    home: function(event) {
        log('HeaderView::home');
        app.navigate("", true);
        return false;
    }
});

var AppRouter = Backbone.Router.extend({
    routes: {
        ""              : "list",
        "trips/new"     : "newTrip",
        "trips/:id"     : "tripDetails"
    },
    
    list: function() {
        log('AppRouter::list');
        if(app.tripView) app.tripView.close();
        this.tripList = new TripCollection();
        var self = this;
        this.tripList.fetch({
            success: function() {
                log('AppRouter::list$success');
                self.tripListView = new TripListView({model: self.tripList});
                self.tripListView.render();
                if(self.requestedId) self.tripDetails(self.requestedId);
            }
        });
    },
    
    newTrip: function() {
        log('AppRouter::newTrip');
        if(!this.tripList) {
            this.list();
        }
        if(app.tripView) app.tripView.close();
        app.tripView = new TripView({model: new Trip()});
        app.tripView.render();
    },
    
    tripDetails: function(id) {
        log('AppRouter::tripDetails(' + id + ')');
        if(this.tripList) {
            log('found tripList');
            this.trip = this.tripList.get(id);
            if(app.tripView) app.tripView.close();
            this.tripView = new TripView({model: this.trip});
            this.tripView.render();
        } else {
            log('did not find tripList');
            this.requestedId = id;
            this.list();
        }
    }
});

var app = new AppRouter();
Backbone.history.start();
var header = new HeaderView();
