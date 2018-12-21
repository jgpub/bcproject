

var PolicyViewModel = function() {
	var that = this;
	this.policySearch = ko.observable();
	this.date = ko.observable(moment(new Date()));

	this.invoices = ko.observable();
	this.payments = ko.observable();
	this.policies = ko.observable();

	this.search = function() {
		var url = "/policies/search?query=" + this.policySearch();
		$.getJSON(url, that.policies);
	}

	this.loadInvoices = function(policy) {
		location.hash = "policy/" + policy.id;
	};

	this.formatDate = function(d) {
		d = moment(d);
		return d.format("MMM D, YYYY");
	}

	this.formatDollarAmount = function(m) {
		if(typeof(m) === 'number') {
			return "$" + m.toFixed(2);
		}
		return "$" + m().toFixed(2);
	};

	this.len = function(x) {
		console.log(x)
		return x().length;
	};

	this.balance = ko.computed(function() {
		var total = 0;
		$.each(that.invoices(), function(i, e) {
			total += e.amount_due;
		});

		$.each(that.payments(), function(i, e) {
			total -= e.amount_paid;
		});
		return total;
	}, this);

	Sammy(function() {
		this.get("#policy/:policy_id", function() {
			var canonicalDate = function(d) {
				console.log(d);
				return d.format(
					"YYYY-MM-DD"
				);
			};
			var url = "/policies/" + this.params.policy_id + "/invoices";
			url += "?date=" + canonicalDate(that.date());			
			$.getJSON(url, that.invoices);

			url = "/policies/" + this.params.policy_id + "/payments";
			$.getJSON(url, that.payments);
		});
	}).run();

} 

ko.bindingHandlers.dateTimePicker = {
    init: function (element, valueAccessor, allBindingsAccessor) {
        //initialize datepicker with some optional options
        // var options = allBindingsAccessor().dateTimePickerOptions || {};
        var options = {
        	format: 'L'
        }
        $(element).datetimepicker(options);

        //when a user changes the date, update the view model
        ko.utils.registerEventHandler(element, "dp.change", function (event) {
            var value = valueAccessor();
            window.valueAccessor = valueAccessor;
            console.log(valueAccessor)
            if (ko.isObservable(value)) {
                if (event.date != null && !(event.date instanceof Date)) {
                	console.log(event)
                    value(event.date);
                } else {
                    value(event.date);
                }
            }
        });

        ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
            var picker = $(element).data("DateTimePicker");
            if (picker) {
                picker.destroy();
            }
        });
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {

        var picker = $(element).data("DateTimePicker");
        //when the view model is updated, update the widget
        if (picker) {
            var koDate = ko.utils.unwrapObservable(valueAccessor());

            //in case return from server datetime i am get in this form for example /Date(93989393)/ then fomat this
            // koDate = (typeof (koDate) !== 'object') ? new Date(parseFloat(koDate.replace(/[^0-9]/g, ''))) : koDate;
            console.log(koDate);
            picker.date(koDate);
        }
    }
};