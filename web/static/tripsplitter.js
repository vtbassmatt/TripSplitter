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

    /// AboutView
    app.AboutView = Backbone.View.extend({
        template: _.template($('#about-content').html()),
        
        initialize: function() {
            log('AboutView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// HelpView
    app.HelpView = Backbone.View.extend({
        template: _.template($('#help-content').html()),
        
        initialize: function() {
            log('HelpView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// ContactView
    app.ContactView = Backbone.View.extend({
        template: _.template($('#contact-content').html()),
        
        initialize: function() {
            log('ContactView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    /// TripsView
    app.TripsView = Backbone.View.extend({
        template: _.template($('#trips-content').html()),
        
        initialize: function() {
            log('TripsView::initialize');
            $(this.el).html(this.template());
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
        show: function(page) {
            log('UiView::show');
            var content_el = $(this.el).children(".content").first();
            switch(page) {
                case "trips":
                    this.content = new app.TripsView({el: content_el});
                    break;
                case "about":
                    this.content = new app.AboutView({el: content_el});
                    break;
                case "contact":
                    this.content = new app.ContactView({el: content_el});
                    break;
                case "help":
                    this.content = new app.HelpView({el: content_el});
                    break;
                default:
                    triggerFatalError("No UI pane to show");
            }
            this.navbar.chooseActiveNavbar(page);
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
