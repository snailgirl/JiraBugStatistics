from jira import JIRA
import sys
import time
import datetime
import os
import yaml

class JiraTool():
    def __init__(self, maxResults = 500):
        self.server = 'http://127.0.0.1:8080'
        self.basic_auth = ('username', 'password')
        # issues查询的最大值
        self.maxResults = maxResults
        self.product_info = self._get_conf().get('product')

    def _get_conf(self):
        """
        获取配置文件
        :return:
        """
        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf', 'jira.yaml')
        conf_file = open(filename, 'r', encoding='utf-8')
        conf_content = yaml.load(conf_file)
        return conf_content

    def login(self):
        self.jira=JIRA(server=self.server, basic_auth=self.basic_auth)
        if self.jira == None:
            print('连接失败')
            sys.exit(-1)

    def __get_bug_jira_modules(self, module):
        """
        从JIRA获取的项目
        :return:
        """
        product_dict = {}
        jql = "component = %s" % module
        try:
            issues = self.jira.search_issues(jql, maxResults=self.maxResults)
        except Exception as e:
            print(e)
            sys.exit(-1)
        for issue in issues:
            projectKey = issue.key.split("-")[0]
            projectName = ""
            if projectKey not in product_dict:
                for key in self.product_info:
                    if self.product_info[key][0] == projectKey:
                        projectName = self.product_info[key][1]
                        break
                product_dict[projectKey] = [module + projectName, 0, 0, 0, 0]
        return product_dict

    def get_bug_module(self, module):
        """
        获取某模块在所有各个项目中的bug总数、未解决数
        :return:
        """
        product_dict = self.__get_bug_jira_modules(module)
        for pid in product_dict:
            project = pid
            # 从JIRA上查找所有问题,不包含重复提交的
            jql = "project=" + project + " AND component = %s and (resolution != Duplicate or resolution=unresolved )" % module
            issues = self.jira.search_issues(jql, maxResults=self.maxResults)
            bug_count = len(issues)
            # 获取这周提交的问题个数
            new_count = self.__get_newbug_count('created', issues)
            # 查找所有已经解决的问题，不包含重复提交的
            # 已关闭数
            # jqlFixed = "project=" + project + " AND component = {} AND status = closed and resolution != Duplicate".format(module)
            # 已解决和已关闭数
            jqlFixed = "project=" + project + " AND component = {} AND status in( resolved,closed) and resolution != Duplicate".format(module)

            fixedIssues = self.jira.search_issues(jqlFixed, maxResults=self.maxResults)
            fixed_bug_count = len(fixedIssues)
            # 获取这周已解决和已关闭的bug数
            newfixed_count = self.__get_newbug_count('updated', fixedIssues)
            product_dict[pid][1] = product_dict[pid][1] + bug_count
            active_count = bug_count - fixed_bug_count
            # 记录仍激活的问题数
            product_dict[pid][2] = active_count
            product_dict[pid][3] = new_count
            product_dict[pid][4] = newfixed_count

            # print(product_dict[project][0], 'bug_count', bug_count)
            # print(product_dict[project][0], 'fixed_bug_count', fixed_bug_count)
            # print(product_dict[project][0], 'newfixed_count', newfixed_count)
            # print(product_dict[project][0], 'active_count', active_count)
        print(module, '：')
        content = self.product_statistics(product_dict, module)  # 生成报告
        return content

    def __get_newbug_count(self, opt, issues):
        """
        获取这周的问题个数
        :param opt: 统计的字段值，日期字段
        :param issues:
        :return:
        """
        count = 0
        tnow = time.time()
        dnow = datetime.datetime.fromtimestamp(tnow)
        for issue in issues:
        #     t = issue.fields.created.split('.')[0]
            try:
                tt = getattr(issue.fields, opt)
            except Exception as e:
                print(e)
                sys.exit(-1)
            t = tt.split('.')[0]
            t1 = time.mktime(time.strptime(t, "%Y-%m-%dT%H:%M:%S"))
            d1 = datetime.datetime.fromtimestamp(t1)
            if (( dnow - d1).days < 7):
                count = count + 1
        return count

    def get_bug_all(self):
        """
        从 JIRA 上查找所有问题,不包含重复提交的
        :return:
        """
        product_all_dict = {}
        for key in self.product_info:
            # 从JIRA上查找所有问题,不包含重复提交的
            jql = "project=" + self.product_info[key][0] + " AND (resolution != Duplicate or resolution=unresolved )"
            issues = self.jira.search_issues(jql, maxResults=10000)
            bug_count = len(issues)
            # 获取这周提交的问题个数
            new_count = self.__get_newbug_count('created', issues)
            # 查找所有已经解决的问题， 不包含重复提交的
            # 已关闭数
            # jqlFixed = "project=" +  self.product_info[key][0] + " AND status = closed and resolution != Duplicate"
            # 已解决和已关闭数
            jqlFixed = "project=" +  self.product_info[key][0] + " AND status in( resolved,closed) and resolution != Duplicate"
            fixedIssues = self.jira.search_issues(jqlFixed, maxResults=10000)
            # 获取这周已解决和已关闭的bug数
            newfixed_count = self.__get_newbug_count('updated', fixedIssues)
            fixed_bug_count = len(fixedIssues)
            active_count = bug_count - fixed_bug_count
            bug_count = len(issues)
            # print (key, bug_count, active_count, new_count)
            product_all_dict[self.product_info[key][0]] = [self.product_info[key][2], bug_count,active_count, new_count, newfixed_count]
        print('总体：')
        content = self.product_statistics(product_all_dict) #生成报告
        return content

    def product_statistics(self, product_dict, module=None):
        """
        生成表格报告
        :param product_dict:
        :param module:
        :return:
        """
        # 将product_dict的Value从[名称, 总Bug数, 激活的Bug数,新增bug数,新关闭bug数]改为[名称, 总Bug数, 激活的Bug数,新增bug数, 新关闭bug数,已解决的Bug数,解决率]
        for pid in product_dict:
            all_num = product_dict[pid][1]
            active_num = product_dict[pid][2]
            fixed_num = all_num - active_num
            if all_num != 0:
                fix_rate = float(fixed_num) / float(all_num) * 100
            else:
                fix_rate = 0.0
            product_dict[pid].append(fixed_num)
            product_dict[pid].append(fix_rate)
        print(product_dict)
        # 按照解决率对product_dict排序，结果变为product_list，每个元素是[名称, 总Bug数, 激活的Bug数,新增bug数, 新关闭bug数, 已解决的Bug数,解决率]
        product_list = sorted(product_dict.values(), key=lambda d: d[6], reverse=True)
        print(product_list)
        # HTML邮件表格开头
        if module:
            content="&nbsp;解决率统计 - " + module+"：<br>"
        else:
            content="&nbsp;解决率统计 - 总体：<br>"
        content += "<table border=\"1\" cellspacing=\"0\" cellpadding=\"0\"><tr align=\"center\">" \
                  + "<th bgcolor='#cc9999' style=\"width:150px\">项目</th>" \
                  + "<th bgcolor='#cc9999' style=\"width:120px\">全部bug</th>" \
                  + "<th bgcolor='#cc9999' style=\"width:120px\">全部已解决bug</th>" \
                  + "<th bgcolor='#cc9999' style=\"width:120px\">本周新增bug</th>" \
                  + "<th bgcolor='#cc9999' style=\"width:130px\">本周已解决bug</th>" \
                  + "<th bgcolor='#cc9999' style=\"width:120px\">bug解决率</th></tr>"
        # 总Bug数和总Bug未解决数
        all_cnt = 0
        fixed_cnt = 0
        new_cnt = 0
        new_fixed_cnt = 0
        # 对每一个产品，输出结果
        for item in product_list:
            # 相关信息
            product_name = item[0]
            all_num = item[1]
            new_num = item[3]
            new_fixed_num = item[4]
            fixed_num = item[5]
            fix_rate = item[6]
            # 统计总数
            all_cnt = all_cnt + all_num
            fixed_cnt = fixed_cnt + fixed_num
            new_cnt = new_cnt + new_num
            new_fixed_cnt = new_fixed_cnt + new_fixed_num
            if all_num != 0:
                print(product_name)
                print("All bugs:\t" + str(all_num))
                print("Fixed bugs:\t" + str(fixed_num))
                print("New Fixed bugs:\t" + str(new_fixed_num))
                print("Fix rate:\t%.2f%%" % fix_rate)
                content += "<tr align=\"center\"><td>" + product_name + "</td><td>" \
                           + str(all_num) + "</td><td>" +  str(fixed_num) + "</td><td>" + \
                           str(new_num) + "</td><td>" + str(new_fixed_num) + "</td><td>" +"%.2f%%" % fix_rate + "</td></tr>"
                print("")
        # 总Bug解决数和总Bug解决率
        fix_rate = float(fixed_cnt) / float(all_cnt) * 100
        print("--------------------\n")
        print("Total")
        print("All bugs:\t" + str(all_cnt))
        print("Fixed bugs:\t" + str(fixed_cnt))
        print("New Fixed bugs:\t" + str(new_fixed_cnt))
        content += "<tr align=\"center\"><td>合计</td><td>" + str(all_cnt) + "</td><td>" +str(fixed_cnt) +\
                   "</td><td>" + str(new_cnt) + "</td><td>" + str(new_fixed_cnt) + "</td><td>"
        if all_cnt != 0:
            print("Fix rate:\t%.2f%%" % fix_rate)
            content += "%.2f%%" % fix_rate + "</td></tr>"
            print("")
        content += "</table>"
        return content

if __name__ == '__main__':
    jiraTool = JiraTool()
    jiraTool.login()
    # 总体bug
    content_total = jiraTool.get_bug_all()