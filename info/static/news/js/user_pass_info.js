function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        e.preventDefault();

        // 修改密码
        var params = {};
        // 因为没有id 或者 class 只有 name 因此需要根据name取值
        // 取到当前表单所需要提交的参数，name 有值的input标签
        // x: {name:"old_password", value: "123456788"}
        $(this).serializeArray().map(function (x) {
            // 取到参数，组装成新的字典

            params[x.name] = x.value;
            // alert("取到的参数是")
            // alert(params)
        });
        // 取到两次密码进行判断
        var new_password = params["new_password"];
        var new_password2 = params["new_password2"];

        if (new_password != new_password2) {
            alert('两次密码输入不一致')
            return
        }

        $.ajax({
            url: "/user/pass_info",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 修改成功
                    alert("修改成功")
                    // 页面重新加载，数显的是iframe当前的小窗口，去掉密码
                    window.location.reload()
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})