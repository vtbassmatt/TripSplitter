var Convenience = function() {
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
}();

var App = {};
(function(app) {

    /// Trip (model)
    app.Trip = Backbone.Model.extend({
        urlRoot: "/api/trip",
        defaults: {
            "id": null,
            "name": "",
            "password": "",
            "start_date": (new Date()).toLocaleDateString(),
            "end_date": (new Date()).toLocaleDateString(),
            "travelers": []
        },
        parse: function(response) {
            log('Trip::parse');
            dates = ["create_date", "end_date", "modify_date", "start_date"];
            for(i in dates) {
                var date = dates[i];
                if(response[date]) {
                    response[date] = (Date.fromJSON(response[date])).toLocaleDateString();
                }
            }
            return response;
        },
        initialize: function() {
            log('Trip::initialize');
            /*this.expenses = new ExpenseCollection();
            var self = this;
            this.expenses.url = function() { 
                if(self.id) return '/api/trip/' + self.id + '/expense';
                throw "Trip must be fetched or saved before expenses URL is valid";
            }*/
        }
    });
    
    /// TripCollection
    app.TripCollection = Backbone.Collection.extend({
        model: app.Trip,
        url: '/api/trip',
        parse: function(response) {
            log('TripCollection::parse');
            for(i in response) {
                app.Trip.prototype.parse(response[i]);
            }
            return response;
        }
    });


    /// AboutPane
    app.AboutPane = Backbone.View.extend({
        template: _.template($('#about-content').html()),
        
        initialize: function() {
            log('AboutPane::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// HelpPane
    app.HelpPane = Backbone.View.extend({
        template: _.template($('#help-content').html()),
        
        initialize: function() {
            log('HelpPane::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// ContactPane
    app.ContactPane = Backbone.View.extend({
        template: _.template($('#contact-content').html()),
        
        initialize: function() {
            log('ContactPane::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// TripListView
    app.TripListView = Backbone.View.extend({
        template: _.template($('#trip-list-content').html()),
        
        initialize: function() {
            log('TripListView::initialize');
            this.el = $('#tripList');
            return this;
        },
        
        render: function() {
            log('TripListView::render');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// TripsPane
    app.TripsPane = Backbone.View.extend({
        template: _.template($('#trips-content').html()),
        
        initialize: function() {
            log('TripsPane::initialize');
            $(this.el).html(this.template());
            this.tripListView = new app.TripListView();
            return this;
        },
        
        render: function() {
            log('TripsPane::render');
            this.tripListView.render();
            return this;
        }
    });
    
    // NavbarItem
    app.NavbarItem = Backbone.Model.extend({});
    
    /// NavbarItemView
    app.NavbarItemView = Backbone.View.extend({
        model: new app.NavbarItem,
        
        template: _.template($('#navbar-item-content').html()),
        
        initialize: function() {
            log('NavbarItemView::initialize');
            return this;
        },
        
        render: function() {
            log('NavbarItemView::render');
            $(this.el).html(this.template(this.model.toJSON()));
            return this;
        }
    });
    
    /// NavbarView
    app.NavbarView = Backbone.View.extend({
        el: $(".nav"),
        
        initialize: function() {
            log('NavbarView::initialize');
            
            $(this.el).empty();
            
            _.each(["Trips","About","Contact","Help"],function(item){
                $(this.el).append(
                    new app.NavbarItemView({
                        el: this.make("li"),
                        model: new app.NavbarItem({
                            link:item.toLowerCase(),
                            name:item
                        })
                    })
                .render().el);
            },this);
            
            return this;
        },
        
        // select the navbar item which should be active
        chooseActiveNavbar: function(link) {
            log('NavbarView::chooseActiveNavbar('+link+')');
            $(this.el).children("li.active").toggleClass("active", false);
            $(this.el).children("li").children('a[href="#'+link+'"]')
                .parent().toggleClass("active", true);
            this.render();
            return this;
        }        
    });
    
    /// UiView
    app.UiView = Backbone.View.extend({
        el: $("#contentpane"),

        initialize: function() {
            log('UiView::initialize');
            // main content pane - initialization triggered by the AppRouter
            this.content = null;
            // top navigation bar
            this.navbar = new app.NavbarView;
            this.navbar.render();
            return this;
            
            // TODO: have the UiView pass the list of content panes
            // into the app and the navbar
        },
        
        // select a UI pane
        show: function(pane) {
            log('UiView::show');
            var content_el = $(this.el).children(".content").first();
            switch(pane) {
                case "trips":
                    this.content = new app.TripsPane({el: content_el});
                    break;
                case "about":
                    this.content = new app.AboutPane({el: content_el});
                    break;
                case "contact":
                    this.content = new app.ContactPane({el: content_el});
                    break;
                case "help":
                    this.content = new app.HelpPane({el: content_el});
                    break;
                default:
                    triggerFatalError("No UI pane to show");
            }
            this.navbar.chooseActiveNavbar(pane);
            this.content.render();
        }
    });
    
    /// AppRouter
    app.AppRouter = Backbone.Router.extend({
        routes: {
            "trip/:id"  : "trip",
            // this goes last since it catches all unmatched routes
            ":uipane"   : "showUi"
        },
        
        showUi: function(uipane) {
            log("AppRouter::showUi("+uipane+")");
            if(_.include(["trips", "contact", "about", "help"], uipane)) {
                app.uiView.show(uipane);
            } else if(uipane == "") {
                this.navigate("trips", true)
            } else {
                triggerFatalError("Unmatched route: " + uipane);
            }
        },
        
        trip: function(id) {
            log("AppRouter::trip");
        },
        
    });
    
    // todo: change this into some kind of nice popover
    var displayErrorMessage = function(errors) {
        if(errors.error) {
            alert(errors.error[0].message);
        } else {
            alert(errors.toString());
        }
    };
    
    var triggerFatalError = function(error_message) {
        triggerNonfatalError(error_message);
        throw "_STOP_";
    };
    
    var triggerNonfatalError = function(error_message) {
        displayErrorMessage({"error":[{"message":error_message}]});
    };
    
    /// aaaaaand go!
    app.uiView = new app.UiView();
    app.router = new app.AppRouter();
    Backbone.history.start();
}(App));
