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

var App = function() {

    var Ui = {
        // top navigation bar
        navBar: $(".nav")
    };
    
    var AboutView = Backbone.View.extend({
        template: _.template($('#about-content').html()),
        
        initialize: function() {
            log('AboutView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    var HelpView = Backbone.View.extend({
        template: _.template($('#help-content').html()),
        
        initialize: function() {
            log('HelpView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    var ContactView = Backbone.View.extend({
        template: _.template($('#contact-content').html()),
        
        initialize: function() {
            log('ContactView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    var TripsView = Backbone.View.extend({
        template: _.template($('#trips-content').html()),
        
        initialize: function() {
            log('TripsView::initialize');
            $(this.el).html(this.template());
            return this;
        }
    });
    
    var UiView = Backbone.View.extend({
        el: $("#contentpane"),

        initialize: function() {
            log('UiView::initialize');
            return this;
        },
        
        // select the navbar item which should be active
        _chooseActiveNavbar: function(link) {
            Ui.navBar.children("li.active").toggleClass("active", false);
            Ui.navBar.children("li").children('a[href="'+link+'"]')
                .parent().toggleClass("active", true);
            return this;
        },
        
        // show the selected UI pane
        _showUi: function(page) {
            log('UiView::showUi');
            var content_el = $(this.el).children(".content").first();
            switch(page) {
                case "trips":
                    this.content = new TripsView({el: content_el});
                    break;
                case "about":
                    this.content = new AboutView({el: content_el});
                    break;
                case "contact":
                    this.content = new ContactView({el: content_el});
                    break;
                case "help":
                    this.content = new HelpView({el: content_el});
                    break;
                default:
                    triggerFatalError("No UI pane to show");
            }
            this.content.render();

            return this;
        },
        
        // public method for selecting a UI pane
        show: function(uipane) {
            log('UiView::show');
            this._chooseActiveNavbar("#"+uipane)
                ._showUi(uipane);
        }
    });

    var AppRouter = Backbone.Router.extend({
        routes: {
            "trip/:id"  : "trip",
            // this goes last since it catches all unmatched routes
            ":uipane"   : "showUi"
        },
        
        showUi: function(uipane) {
            log("AppRouter::showUi("+uipane+")");
            if(_.include(["trips", "contact", "about", "help"], uipane)) {
                uiView.show(uipane);
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
    var handleFatalError = function(errors) {
        if(errors.error) {
            alert(errors.error[0].message);
        } else {
            alert(errors.toString());
        }
    };
    
    var triggerFatalError = function(error_message) {
        handleFatalError({"error":[{"message":error_message}]});
        throw "_STOP_";
    };
    
    var uiView = new UiView();
    var router = new AppRouter();
    Backbone.history.start();
}();
