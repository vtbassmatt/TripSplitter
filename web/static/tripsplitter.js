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
        navBar: $(".nav"),
        // main UI panes
        trips: $("#trips"),
        about: $("#about"),
        contact: $("#contact"),
        help: $("#help")
    };
    
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
        
        // hide all the UI panes
        _hideAllUi: function() {
            log('UiView::hideAllUi');
            Ui.trips  .toggleClass("hide", true);
            Ui.about  .toggleClass("hide", true);
            Ui.contact.toggleClass("hide", true);
            Ui.help   .toggleClass("hide", true);
            return this;
        },
        
        // reveal only the selected UI pane
        _showUi: function(page) {
            log('UiView::showUi');
            Ui[page].toggleClass("hide", false);
            return this;
        },
        
        // public method for selecting a UI pane
        show: function(uipane) {
            log('UiView::show');
            this._chooseActiveNavbar("#"+uipane)
                ._hideAllUi()
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
                handleFatalError({"error":[{"message":"Unmatched route: " + uipane}]});
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
    
    var uiView = new UiView();
    var router = new AppRouter();
    Backbone.history.start();
}();
