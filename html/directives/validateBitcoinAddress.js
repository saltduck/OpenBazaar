angular.module('app').directive("validateBitcoinAddress", function() {
    return {
        require: 'ngModel',
        link: function(scope, ele, attrs, ctrl) {

            ctrl.$parsers.unshift(function(value) {

                // test and set the validity after update.
                var valid = window.bitcoinAddress.validate(value);
                ctrl.$setValidity('validateBitcoinAddress', valid);

                // if it's valid, return the value to the model,
                // otherwise return undefined.
                return valid ? value : undefined;
            });

            ctrl.$formatters.unshift(function(value) {
                // validate.
                ctrl.$setValidity('validateBitcoinAddress', window.bitcoinAddress.validate(value));

                // return the value or nothing will be written to the DOM.
                return value;
            });


        }
    };

});
