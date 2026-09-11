
var R = global


// i[Jt]
function p_(t) {
    t = R["encodeURIComponent"](t)["replace"](/%([0-9A-F]{2})/g, function (n, t) {
        return o("0x" + t)
    });
    try {
        return R["btoa"](t)
    } catch (n) {
        return R[W5][K5](t)[U5](Z5)
    }
}


//o
function o(n) {
    t = "",
        ['66', '72', '6f', '6d', '43', '68', '61', '72', '43', '6f', '64', '65']["forEach"](function (n) {
            t += R["unescape"]("%u00" + n)
        });
    var t, e = t;
    return R["String"][e](n)
}

// i[Qt]
function h_(n, t) {
    t = t || u();
    for (var e = (n = n["split"](""))["length"], r = t["length"], a = "charCodeAt", i = 0; i < e; i++)
        n[i] = o(n[i][a](0) ^ t[(i + 10) % r][a](0));
    return n["join"]("")
}



//r
r = +new R["Date"] - (4677 || 0) - 1661224081041

/*
//a
var a =[
    3,
    "2026-08-14",
    "2026-08-14",
    "2026-08-14",
    "cn",
    "36",
    4,
    3
]
a = a["sort"]()["join"]("")
a =  p_(a)
a = (a += "@#" + "/rank/offline") + ("@#" + r) + ("@#" + 3)

//d
//d = i[zt](Bt, B)

//原始加密函数： e = (0,i[Jt])((0,i[Qt])(a, d)),
var d = "xyz517cda96efgh"
var e = p_(h_(a, d))
console.log(e)
*/
function pagesource(page){
    var a =[
    3,
    "2026-08-14",
    "2026-08-14",
    "2026-08-14",
    "cn",
    "36",
    4,
    page
]
    a = a["sort"]()["join"]("")
    a =  p_(a)
    a = (a += "@#" + "/rank/offline") + ("@#" + r) + ("@#" + 3)
    var d = "xyz517cda96efgh"
    var e = p_(h_(a, d))
    return e
}

// console.log(pagesource(1))
// console.log(pagesource(2))