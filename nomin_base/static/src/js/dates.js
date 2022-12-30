
(function() {

var instance = openerp;

var _t = instance.web._t;
/**
 * Converts a string to a Date javascript object using OpenERP's
 * datetime string format (exemple: '2011-12-01 15:12:35').
 * 
 * The time zone is assumed to be UTC (standard for OpenERP 6.1)
 * and will be converted to the browser's time zone.
 * 
 * @param {String} str A string representing a datetime.
 * @returns {Date}
 */
instance.web.str_to_datetime = function(str) {
    if(!str) {
        return str;
    }
    var regex = /^(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d(?:\.(\d+))?)$/;
    var res = regex.exec(str);
    if ( !res ) {
        throw new Error(_t("'%s' is not a valid datetime"), str);
    }
//    var tmp = new Date(2000,0,1);
//    tmp.setUTCMonth(1970);
//    tmp.setUTCMonth(0);
//    tmp.setUTCDate(1);
//    tmp.setUTCFullYear(parseFloat(res[1]));
//    tmp.setUTCMonth(parseFloat(res[2]) - 1);
//    tmp.setUTCDate(parseFloat(res[3]));
//    tmp.setUTCHours(parseFloat(res[4]));
//    tmp.setUTCMinutes(parseFloat(res[5]));
//    tmp.setUTCSeconds(parseFloat(res[6]));
//    tmp.setUTCSeconds(parseFloat(res[6]));
//    tmp.setUTCMilliseconds(parseFloat(rpad((res[7] || "").slice(0, 3), 3)));
    tmp = Date.parseExact(res[0], 'yyyy-MM-dd HH:mm:ss');
    return tmp;
};
	

/**
 * Converts a string to a Date javascript object using OpenERP's
 * date string format (exemple: '2011-12-01').
 * 
 * As a date is not subject to time zones, we assume it should be
 * represented as a Date javascript object at 00:00:00 in the
 * time zone of the browser.
 * 
 * @param {String} str A string representing a date.
 * @returns {Date}
 */
instance.web.str_to_date = function(str) {
    if(!str) {
        return str;
    }
    var regex = /^(\d\d\d\d)-(\d\d)-(\d\d)$/;
    var res = regex.exec(str);
    if ( !res ) {
        throw new Error(_("'%s' is not a valid date"), str);
    }
    var tmp = new Date(2000,0,1);
    tmp.setFullYear(parseFloat(res[1]));
    tmp.setMonth(parseFloat(res[2]) - 1);
    tmp.setDate(parseFloat(res[3]));
    tmp.setHours(0);
    tmp.setMinutes(0);
    tmp.setSeconds(0);
    return tmp;
};

/**
 * Converts a string to a Date javascript object using OpenERP's
 * time string format (exemple: '15:12:35').
 * 
 * The OpenERP times are supposed to always be naive times. We assume it is
 * represented using a javascript Date with a date 1 of January 1970 and a
 * time corresponding to the meant time in the browser's time zone.
 * 
 * @param {String} str A string representing a time.
 * @returns {Date}
 */
instance.web.str_to_time = function(str) {
    if(!str) {
        return str;
    }
    var regex = /^(\d\d:\d\d:\d\d)(?:\.\d+)?$/;
    var res = regex.exec(str);
    if ( !res ) {
        throw new Error(_.str.sprintf(_t("'%s' is not a valid time"), str));
    }
    var obj = Date.parseExact("1970-01-01 " + res[1], 'yyyy-MM-dd HH:mm:ss');
    if (! obj) {
        throw new Error(_.str.sprintf(_t("'%s' is not a valid time"), str));
    }
    return obj;
};

/*
 * Left-pad provided arg 1 with zeroes until reaching size provided by second
 * argument.
 *
 * @param {Number|String} str value to pad
 * @param {Number} size size to reach on the final padded value
 * @returns {String} padded string
 */
var lpad = function(str, size) {
    str = "" + str;
    return new Array(size - str.length + 1).join('0') + str;
};

var rpad = function(str, size) {
    str = "" + str;
    return str + new Array(size - str.length + 1).join('0');
};

/**
 * Converts a Date javascript object to a string using OpenERP's
 * datetime string format (exemple: '2011-12-01 15:12:35').
 * 
 * The time zone of the Date object is assumed to be the one of the
 * browser and it will be converted to UTC (standard for OpenERP 6.1).
 * 
 * @param {Date} obj
 * @returns {String} A string representing a datetime.
 */
instance.web.datetime_to_str = function(obj) {
    if (!obj) {
        return false;
    }
    /*
    return zpad(obj.getUTCFullYear(),4) + "-" + zpad(obj.getUTCMonth() + 1,2) + "-"
         + zpad(obj.getUTCDate(),2) + " " + zpad(obj.getUTCHours(),2) + ":"
         + zpad(obj.getUTCMinutes(),2) + ":" + zpad(obj.getUTCSeconds(),2);
    */
    return lpad(obj.getFullYear(),4) + "-" + lpad(obj.getMonth() + 1,2) + "-"
        + lpad(obj.getDate(),2) + " " + lpad(obj.getHours(),2) + ":"
        + lpad(obj.getMinutes(),2) + ":" + lpad(obj.getSeconds(),2);
};

/**
 * Converts a Date javascript object to a string using OpenERP's
 * date string format (exemple: '2011-12-01').
 * 
 * As a date is not subject to time zones, we assume it should be
 * represented as a Date javascript object at 00:00:00 in the
 * time zone of the browser.
 * 
 * @param {Date} obj
 * @returns {String} A string representing a date.
 */
instance.web.date_to_str = function(obj) {
    if (!obj) {
        return false;
    }
    return lpad(obj.getFullYear(),4) + "-" + lpad(obj.getMonth() + 1,2) + "-"
         + lpad(obj.getDate(),2);
};

/**
 * Converts a Date javascript object to a string using OpenERP's
 * time string format (exemple: '15:12:35').
 * 
 * The OpenERP times are supposed to always be naive times. We assume it is
 * represented using a javascript Date with a date 1 of January 1970 and a
 * time corresponding to the meant time in the browser's time zone.
 * 
 * @param {Date} obj
 * @returns {String} A string representing a time.
 */
instance.web.time_to_str = function(obj) {
    if (!obj) {
        return false;
    }
    return lpad(obj.getHours(),2) + ":" + lpad(obj.getMinutes(),2) + ":"
         + lpad(obj.getSeconds(),2);
};
    
})();
