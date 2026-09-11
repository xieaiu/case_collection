window = global;
require('./mod')
var crypto_js = require("crypto-js")


function get_sign(room_id) {
    // 字符串中的room_id是动态的, 需要将形参嵌入到字符串中
    let o = `live_id=1,aid=6383,version_code=180800,webcast_sdk_version=1.0.14-beta.0,room_id=${room_id},sub_room_id=,sub_channel_id=,did_rule=3,user_unique_id=7534719531689707046,device_platform=web,device_type=,ac=,identity=audience`
    let a = crypto_js.MD5(o).toString()
    // console.log(l);

    // 生成sign值
    let sign = window.loader({
        "X-MS-STUB": a
    })
    console.log(sign['X-Bogus'])
    return sign['X-Bogus']
}

//测试示例
// get_sign(7535464634804210458)



