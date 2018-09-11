function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pic_info").submit(function (e) {
        e.preventDefault()

        //上传头像
        // ajaxSubmit 代表使用 jquery 的代码去模拟点击提交按钮的操作
        // 自动拼接并，提交当前的参数(因为当前数据是文件，手动拼接费劲)
        // 要使用 必须导入jquery和 jquery.form.main.js
        $(this).ajaxSubmit({
            url: "/user/pic_info",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                        // alert("0")
                if (resp.errno == "0") {
                    $(".now_user_pic").attr("src", resp.data.avatar_url)
                    $(".user_center_pic>img", parent.document).attr("src", resp.data.avatar_url)
                    $(".user_login>img", parent.document).attr("src", resp.data.avatar_url)
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})