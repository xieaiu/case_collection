//原始解密函数

function decrypt(e) {
    let t = new Uint8Array;
    t = "base64" === this.cipherType ? o.base64ToArrayBuffer(e) : o.stringToArrayBufferInUtf8(e);
    let n = t.length / r
        , i = new Uint8Array(t.length);
    if ("cbc" === this.mode) {
        if (null === this.iv || 16 !== this.iv.length)
            throw new Error("iv error");
        let e = this.uint8ToUint32Block(this.iv);
        for (let o = 0; o < n; o++) {
            let n = o * r
                , s = this.uint8ToUint32Block(t, n)
                , a = this.doBlockCrypt(s, this.decryptRoundKeys)
                , l = new Uint32Array(4);
            l[0] = e[0] ^ a[0],
                l[1] = e[1] ^ a[1],
                l[2] = e[2] ^ a[2],
                l[3] = e[3] ^ a[3],
                e = s;
            for (let e = 0; e < r; e++)
                i[n + e] = l[parseInt(e / 4)] >> (3 - e) % 4 * 8 & 255
        }
    } else
        for (let o = 0; o < n; o++) {
            let e = o * r
                , n = this.uint8ToUint32Block(t, e)
                , s = this.doBlockCrypt(n, this.decryptRoundKeys);
            for (let t = 0; t < r; t++)
                i[e + t] = s[parseInt(t / 4)] >> (3 - t) % 4 * 8 & 255
        }
    let s = this.dePadding(i);
    return o.utf8ArrayBufferToString(s)
}

