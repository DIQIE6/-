import requests
import tkinter as tk
from tkinter import ttk
import threading
import time

# 配置请求头（登录）
login_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "channel-type": "student-id-number",
    "Host": "221.231.125.178:19702",
    "Origin": "http://221.231.125.178:19702",
    "Proxy-Connection": "keep-alive",
    "Referer": "http://221.231.125.178:19702/"
}

# 配置请求头（选课）
course_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "channel-type": "student-id-number",
    "Host": "221.231.125.178:19702",
    "Origin": "http://221.231.125.178:19702",
    "Proxy-Connection": "keep-alive",
    "Referer": "http://221.231.125.178:19702/",
}

# 配置请求体
login_data = {}

# 初始化会话
session = requests.Session()

# 登录过程
def login():
    global login_data
    username = username_entry.get()
    password = password_entry.get()
    login_data = {
        "channel-type": "student-id-number",
        "username": username,
        "password": password
    }
    
    try:
        login_response = session.post("http://221.231.125.178:19702/basicVisitor/login", headers=login_headers, data=login_data)
        
        if login_response.status_code == 200:
            append_to_output("登录成功！\n")
            
            # 提取 token
            if 'hope-access-token' in login_response.headers:
                token = login_response.headers['hope-access-token']
                session.headers.update({'hope-access-token': token}) 
            else:
                append_to_output("未找到 Token\n")
                return False
            get_courses()  # 登录成功后直接获取课程
        else:
            append_to_output(f"登录失败，状态码: {login_response.status_code}\n")
            append_to_output(f"响应内容: {login_response.text}\n")
            return False
    except requests.exceptions.RequestException as e:
        append_to_output(f"请求失败: {e}\n")
        return False

# 获取课程列表
def get_courses():
    get_courses_url = "http://221.231.125.178:19702/basicVisitor/zncgVisitor/getCourses"
    try:
        courses_response = session.get(get_courses_url, headers=login_headers)
        
        if courses_response.status_code == 200:
            courses_data = courses_response.json()
            
            if "physicalEducationInfoManageList" in courses_data:
                courses = courses_data["physicalEducationInfoManageList"]
                display_courses(courses)  # 显示课程列表
            else:
                append_to_output("未找到课程列表\n")
        else:
            append_to_output(f"获取课程列表失败，状态码: {courses_response.status_code}\n")
            append_to_output(f"响应内容: {courses_response.text}\n")
    except requests.exceptions.RequestException as e:
        append_to_output(f"请求失败: {e}\n")

# 显示课程列表，并允许选择
def display_courses(courses):
    global course_combobox
    for widget in course_frame.winfo_children():
        widget.destroy()

    course_names = [course.get("courseClassifyName", "未知课程") for course in courses]

    # 创建一个下拉框显示所有课程
    course_combobox = ttk.Combobox(course_frame, values=course_names, width=40)
    course_combobox.pack(pady=10)

    # 添加开始抢课按钮
    start_button = tk.Button(course_frame, text="开始抢课", command=lambda: start_save_course(courses))
    start_button.pack(pady=5)

# 开始抢课
def start_save_course(courses):
    selected_course_name = course_combobox.get()

    # 查找选中的课程ID
    selected_course = next((course for course in courses if course.get("courseClassifyName") == selected_course_name), None)
    
    if selected_course:
        selected_course_id = selected_course["physicalEducationId"]
        append_to_output(f"选择的课程名称: {selected_course_name}\n")
        # 使用线程开始抢课
        threading.Thread(target=save_course, args=(selected_course_id,)).start()
    else:
        append_to_output("未找到选中的课程\n")

# 提交选课请求
def save_course(selected_course_id):
    save_course_url = "http://221.231.125.178:19702/basicVisitor/zncgVisitor/saveCourseSelection"
    course_data = {
        "physicalEducationInfoId": selected_course_id
    }

    try:
        try_count = 1
        while True:
            save_response = session.post(save_course_url, headers=course_headers, json=course_data)
            append_to_output(f"第{try_count}次请求响应：{save_response.text}\n")  # 打印每次请求的响应内容

            if "逻辑班不存在！" or '选课时间已过' in save_response.text: # 这个响应比较神奇
                append_to_output("课程已被抢完，停止请求。\n")
                break  # 停止选课请求

            try_count += 1
            time.sleep(0.01)  # 每次请求间隔10ms

    except requests.exceptions.RequestException as e:
        append_to_output(f"请求失败: {e}\n")

# 输出信息到GUI
def append_to_output(text):
    output_text.insert(tk.END, text)  # 在Text控件中插入文本
    output_text.yview(tk.END)  # 自动滚动到最新内容

# 设置GUI
root = tk.Tk()
root.title("抢课程序")
root.geometry("600x500")

# 用户名输入框
username_label = tk.Label(root, text='用户名')
username_label.pack(pady=5)
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

# 密码输入框
password_label = tk.Label(root, text='密码')
password_label.pack(pady=5)
password_entry = tk.Entry(root, width=30, show="*")
password_entry.pack(pady=5)

# 登录按钮
login_button = tk.Button(root, text="登录", command=login)
login_button.pack(pady=10)

# 课程选择框（初始化为空，动态填充）
course_frame = tk.Frame(root)
course_frame.pack(pady=20)

# 输出显示框
output_text = tk.Text(root, width=70, height=10)
output_text.pack(pady=20)

root.mainloop()
