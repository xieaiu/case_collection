function W() {
    var t = n[161];
    var r = qn.update();   // 同步计算，保留原返回值
    console.log("[RPC] W called; qn length=" + (r && r.length));

    const websocket = new WebSocket('ws://127.0.0.1:8080/');

    websocket.onopen = function () {
        console.log("[RPC] WebSocket open");
        websocket.send(r);
    };

    websocket.onmessage = function (event) {
        console.log("[RPC] server reply: " + event.data);
    };

    websocket.onerror = function () {
        console.log("[RPC] WebSocket error");
    };

    websocket.onclose = function () {
        console.log("[RPC] WebSocket closed");
    };

    Wn.setCookie(On, r, m + Rn + w + t, E, n[162]);
    $n.set(Pn, r);

    return r;
}
