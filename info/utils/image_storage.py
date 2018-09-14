from qiniu import Auth, put_data

access_key = "08q5okTBC7Kt15-qp3tv_KlQxguQ0WgBQ-_Unzn7"
secret_key = "uPUHPc-PkOsXlR99_r1WoF7w-o1jRWHa9h-sw9N0"
bucket_name = "ihome"

# data为长传的二进制文件
def storage(data):
    try:
        # 七牛云认证
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        # 上传成功后，将ret字典中的key对应的值返回，拼接成新的url,就可以直接访问图片,将key保存到本地服务器的mysql中。
        # 接收的第二个参数是文件的名字，一般默认不传，让七牛自己给文件起名字
        ret, info = put_data(token, None, data)
        # print(ret, info)
    except Exception as e:
        raise e

    if info.status_code != 200:
        raise Exception("上传图片失败")
    # 返回七牛给文件起的名字
    # print("上传图片成功")
    print(ret["key"])
    return ret["key"]


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read())