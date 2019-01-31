#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
from libs import send_mail
from libs.jiraTool import *
import configparser

def get_param(param):
    """
    从配置文件中相应信息
    :return:
    """
    sys_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(sys_path)
    sfile_path = os.path.join(sys_path, 'conf', 'conf.ini')
    if not os.path.exists(sfile_path):
        print("Error: %s doesn't exist" % sfile_path)
        sys.exit(-1)
    conf = configparser.ConfigParser()
    conf.read(sfile_path, encoding='utf-8')
    try:
        recv_list = conf.get('conf', param).split(',')
    except Exception as e:
        print("Error:", e)
        sys.exit(-2)
    return recv_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', required=False, help='MAILTO_LIST', default='tester@123.com')
    parser.add_argument('-m', '--module', required=False, help='RPODUCT_MODULE', default='医疗')
    args = parser.parse_args()
    # 获取收件人
    to_list_str = args.list
    to_list = to_list_str.split()
    if get_param('email')[0]:
        to_list = get_param('email')
    print('收件人：', to_list)
    # 获取项目模块
    module_list = args.module.split()
    if get_param('module')[0]:
        module_list= get_param('module')
    print('统计模块：', module_list)
    jiratool = JiraTool()
    jiratool.login()
    # 总体bug
    content_total = jiratool.get_bug_all()
    # 某模块bug:
    content_module = ''
    for module in module_list:
        content_module_temp = jiratool.get_bug_module(module)
        content_module = content_module + content_module_temp + '<br><br>'
    # 发送邮件
    subject = "解决率统计"
    content = content_total+'<br><br>' + content_module  # 邮件内容
    send_mail_obj = send_mail.SendMail()
    status = send_mail_obj.send_mail(to_list, subject, content)
    if status:
        print("Succeed in sending mails\n")
    else:
        print("Failed to send mails\n")

if __name__ == "__main__":
    main()

