import json
import math
import os
import time

import requests

import afdian
from logger import logger

try:
    from flask import Flask, request, Response
except:
    logger.error("未找到flask模块")

try:
    from gevent import pywsgi
except:
    logger.error("未找到gevent模块")
try:
    from dotenv import load_dotenv
except:
    logger.error("未找到dotenv模块")
app = Flask(__name__)

# 添加请求日志中间件
@app.before_request
def log_request_info():
    logger.info('请求信息:')
    logger.info(f'请求方法: {request.method}')
    logger.info(f'请求URL: {request.url}')
    logger.info(f'请求头: {dict(request.headers)}')
    if request.is_json:
        logger.info(f'请求体: {request.get_json()}')
    elif request.form:
        logger.info(f'表单数据: {request.form}')
    elif request.data:
        logger.info(f'原始数据: {request.get_data()}')
    logger.info('-------------------------')

# 添加响应日志中间件
@app.after_request
def log_response_info(response):
    logger.info('响应信息:')
    logger.info(f'状态码: {response.status}')
    logger.info(f'响应头: {dict(response.headers)}')
    logger.info('-------------------------')
    return response

# 初始化检查
def check():
    # 判断.env文件是否存在
    if os.path.exists('.env'):
        if os.environ.get('SITE_URL') == "":
            logger.error("SITE_URL未设置,已停止运行")
            exit()
        if os.environ.get('USER_ID') == "":
            logger.error("USER_ID未设置,已停止运行")
            exit()
        if os.environ.get('TOKEN') == "":
            logger.error("TOKEN未设置,已停止运行")
            exit()
        if os.environ.get('PORT') == "":
            logger.error("PORT未设置,已停止运行")
            exit()
        logger.info("初始化检查通过")
        return
    else:
        logger.error("未找到.env文件,已停止运行")
        exit()


@app.route('/afdian', methods=['POST'])
def respond():
    # 解析返回的json值
    data = request.get_data()
    data = json.loads(data)['data']['order']
    out_trade_no = data['out_trade_no']
    # 获取订单信息（remark）
    order_no = data['remark']
    # 获取订单amount
    afd_amount = str(data['total_amount']).split(".")[0]
    afd_amount = int(afd_amount)
    logger.info(f"收到爱发电回调 - 订单号: {order_no}, 金额: {afd_amount}")
    
    # 查询订单
    amount = 0
    notify_url = ""
    raw = afdian.check_order(order_no, out_trade_no)
    if raw[1] != 0:
        amount = raw[1]
    if afd_amount == int(amount):
        # 订单金额相同
        # 通知网站
        notify_url = raw[2]
        url = notify_url
        # 发送get请求
        requests.get(url)
        logger.info(f"订单验证成功，已发送通知 - 订单号: {order_no}")
    else:
        logger.warning(f"订单金额不匹配 - 订单号: {order_no}, 期望金额: {amount}, 实际金额: {afd_amount}")
    
    # json格式化
    back = '{"ec":200,"em":""}'
    json.dumps(back, ensure_ascii=False)
    return Response(back, mimetype='application/json')


@app.route('/order/create', methods=['post'])
def order():
    load_dotenv('.env')
    # 删除SITE_URL尾部的"/"
    if os.environ.get('SITE_URL')[-1] == "/":
        os.environ['SITE_URL'] = os.environ.get('SITE_URL')[:-1]
    # 读取请求头中的X-Cr-Site-Url
    site_url = request.headers.get('X-Cr-Site-Url')
    if site_url != os.environ.get('SITE_URL'):
        logger.warning(f"站点URL验证失败 - 期望: {os.environ.get('SITE_URL')}, 实际: {site_url}")
        back = {"code": 412, "error": "验证失败，请检查.env文件"}
        back = json.dumps(back, ensure_ascii=False)
        return Response(back, mimetype='application/json')
    
    # 获取Authorization
    authorization = request.headers.get('Authorization').split("Bearer")[1].strip()
    timestamp = authorization.split(":")[1]
    t = str(int(time.time()))
    if t > timestamp:
        logger.warning("时间戳验证失败")
        back = {"code": 412, "error": "时间戳验证失败"}
        return Response(back, mimetype='application/json')
    
    # 读取post内容
    data = request.get_data()
    # 解析json
    data = json.loads(data)
    order_no = data['order_no']
    amount = data['amount']
    # 金额处理
    amount = math.ceil(amount)
    if amount < 500:
        logger.warning(f"订单金额过小 - 订单号: {order_no}, 金额: {amount}")
        back = {"code": 417, "error": "金额需要大于等于5元"}
        back = json.dumps(back, ensure_ascii=False)
        return Response(back, mimetype='application/json')
    
    notify_url = data['notify_url']
    order_info = {"order_no": order_no, "amount": amount, "notify_url": notify_url}
    # json格式化order_info
    order_info = json.dumps(order_info, ensure_ascii=False)
    order_url = afdian.new_order(order_info, amount)
    logger.info(f"创建新订单 - 订单号: {order_no}, 金额: {amount}")
    
    back = {
        "code": 0,
        "data": order_url
    }
    # json格式化back
    back = json.dumps(back, ensure_ascii=False)
    return Response(back, mimetype='application/json')


# 初始化检查
check()

logger.info("Cloudreve Afdian Pay Server 已启动")
logger.info("Github: https://github.com/essesoul/Cloudreve-AfdianPay")
logger.info("-------------------------")
load_dotenv('.env')
port = str(os.getenv('PORT'))
logger.info(f"程序运行端口：{port}")
server = pywsgi.WSGIServer(('0.0.0.0', int(port)), app)
server.serve_forever()
