var crypto_js = require("crypto-js")

var window = global

function encode_HmacSHA512(text, key) {
    return crypto_js.HmacSHA512(text, key).toString();
}


var a_default = {
    "n": 20,
    "codes": {
        "0": "W",
        "1": "l",
        "2": "k",
        "3": "B",
        "4": "Q",
        "5": "g",
        "6": "f",
        "7": "i",
        "8": "i",
        "9": "r",
        "10": "v",
        "11": "6",
        "12": "A",
        "13": "K",
        "14": "N",
        "15": "k",
        "16": "4",
        "17": "L",
        "18": "1",
        "19": "8"
    }
}

function o_default() {
    for (var e = (arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : "/").toLowerCase(), t = e + e, n = "", i = 0; i < t.length; ++i) {
        var o = t[i].charCodeAt() % a_default.n;
        n += a_default.codes[o]
    }
    return n
}

function get_i() {
    var e = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : {}
        , t = (arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : "/").toLowerCase()
        , n = JSON.stringify(e).toLowerCase();
    return encode_HmacSHA512(t + n, o_default(t)).toLowerCase().substr(8, 20)
}


function get_l() {
    var e = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : {}
        , t = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : ""
        , n = (arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : "/").toLowerCase()
        , i = JSON.stringify(e).toLowerCase();
    return encode_HmacSHA512(n + "pathString" + i + t, o_default(n))
}


function s_default() {
                var list = ["w", "i", "n", "d", "o", "w", ".", "t", "i", "d"]; //window.tid
                return eval(list.join(""))
            }


function get_pageinfo(page) {
    var data = {
        "searchKey": "小米",
        "pageIndex": page,
        "pageSize": 20
    }
    var headers = {}
    var t = "/api/search/searchmulti"
    var i = get_i(t, data)
    var l = get_l(t, data, '1177adc16d2167cb61ca042cb1bb5f13'); //字符串由s_default得来：window.tid，需要访问网页文档拿到该值
    headers['key'] = i;
    headers['value'] = l;
    return headers;
}

// console.log(get_pageinfo(1))