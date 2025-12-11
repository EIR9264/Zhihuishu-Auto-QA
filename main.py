# -*- coding: utf-8 -*-
import time
import sys
import json
import os
import io
import random

# 设置默认编码为 UTF-8，解决 Windows 上的编码问题
if sys.platform == "win32":
    import locale

    # 设置标准输入输出编码
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")
    # 设置环境变量，让文件读取使用 UTF-8
    os.environ["PYTHONIOENCODING"] = "utf-8"
# 修复 reloading 库在 Windows 上的编码问题（必须在导入 reloading 装饰器之前执行）
if sys.platform == "win32":
    import importlib

    def patch_reloading_module():
        """修补 reloading 模块的 load_file 函数"""
        try:
            # 导入 reloading.reloading 模块
            reloading_module = importlib.import_module("reloading.reloading")
            # 替换 load_file 函数为使用 UTF-8 编码的版本
            if hasattr(reloading_module, "load_file"):

                def load_file_utf8(path):
                    """使用 UTF-8 编码读取文件，修复 Windows 上的编码问题"""
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()

                # 直接替换函数
                reloading_module.load_file = load_file_utf8
                return True
        except Exception as e:
            print(f"警告: 无法修复 reloading 库的编码问题: {e}")
            return False

    # 先导入 reloading 包
    import reloading

    # 修补模块
    if patch_reloading_module():
        print("已修复 reloading 库的编码问题")

from reloading import reloading

# 导入装饰器后再次确保修补（防止模块被重新加载）
if sys.platform == "win32":
    patch_reloading_module()
from selenium.webdriver import Chrome, Edge, chrome, edge
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from openai import OpenAI

from secret import api_key

with open("./config.json") as f:
    config = json.load(f)

provider = ["deepseek", "siliconflow"][1]  # 切换平台, 须在config.json文件中平台相关配置
base_url = config[provider]["base_url"]
model_name = config[provider]["model_name"]
brower = input("浏览器选择 (默认Edge，输入0使用Chrome):")
if brower.strip() == "0":
    print("正在启动Chrome")
    options = chrome.options.Options()
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=OFF")
    # 使用本地的 chromedriver.exe
    driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    driver = Chrome(
        service=chrome.service.Service(executable_path=driver_path, log_path="nul"),
        options=options,
    )
else:
    print("正在启动Edge")
    options = edge.options.Options()
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=OFF")
    # 使用本地的 msedgedriver.exe
    driver_path = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")
    driver = Edge(
        service=edge.service.Service(executable_path=driver_path, log_path="nul"),
        options=options,
    )

driver.get("https://onlineweb.zhihuishu.com/")
print("已导航至智慧树学生首页, 请自行登录")

ai_client = OpenAI(api_key=api_key, base_url=base_url)


def check() -> bool:
    try:
        if "课程问答" not in driver.title:
            print("检测到当前不在问答页, 正尝试在其他页面中查找问答页")
            all_windows = driver.window_handles
            for window in all_windows:
                driver.switch_to.window(window)  # 逐个窗口切换
                if "课程问答" in driver.title:
                    print("成功切换到课程问答页面")
                    return True
            else:
                print("未找到课程问答页面, 请打开课程问答页面")
                return False
        else:
            return True
    except Exception:  # 当前页已被关闭
        print("检测到当前不在问答页, 正尝试在其他页面中查找问答页")
        try:
            all_windows = driver.window_handles
        except Exception:  # driver已被关闭
            print("当前浏览器已被关闭, 程序无法继续执行, 正在退出")
            driver.quit()
            sys.exit(1)
        for window in all_windows:  # 逐个窗口找
            driver.switch_to.window(window)
            if "课程问答" in driver.title:
                print("成功切换到课程问答页面")
                return True
        else:
            print("未找到课程问答页面, 请打开课程问答页面")
            return False


def check_CAPTCHA():
    try:
        time.sleep(0.5)
        driver.find_element(By.CLASS_NAME, "yidun_modal")
        input("出现验证码, 请手动完成后按回车键继续")
    except Exception:
        pass


@reloading
def ask():
    if not check():
        return
    course_name = driver.find_element(By.CLASS_NAME, "course-name").text
    print(f"课程名: {course_name}, 接下来将获取本页面前30个问题并发给AI分析")
    print("鉴于智慧树的屏蔽机制, 建议提问总数量在15个以上 (10个有效提问为有效计分上限)")
    asks = int(input("请输入本次提问数量: "))
    print("正在获取页面中的问题并发给AI分析")
    question_elements = driver.find_elements(By.CLASS_NAME, "question-content")[:30]
    question_text = ""
    for question in question_elements:
        question_text += question.text + "\n"  # 将所有元素的文本合并
    ai_question = (
        f"请根据提供的例子生成同领域相近但不相同的问题, 要求生成{asks}个, 以下为例子:\n"
        + question_text
    )
    ai_response = ai_client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "你会收到很多问题作为样例, 你要根据提供的例子输出一定数量同领域相近但不相同的问题, 输出的问题数量将由用户指定, 单个问题需要在一行内不换行输出, 不要带有编号或序号, 输出的问题以换行分隔, 不要使用Markdown或LaTeX语法, 切记要遵循问题数量",
            },
            {"role": "user", "content": ai_question},
        ],
        temperature=0.2,
    )
    questions_list = ai_response.choices[0].message.content.split("\n")[:asks]
    print("\n以下为AI生成的提问:")
    for question in questions_list:
        print(question)
    # 获取时间间隔设置
    min_delay_input = input("\n最小时间间隔（不填默认2秒）: ").strip()
    try:
        min_delay = float(min_delay_input) if min_delay_input else 2.0
    except ValueError:
        print("输入无效，使用默认值2秒")
        min_delay = 2.0
    max_delay_input = input("最大时间间隔（不填默认5秒）: ").strip()
    try:
        max_delay = float(max_delay_input) if max_delay_input else 5.0
    except ValueError:
        print("输入无效，使用默认值5秒")
        max_delay = 5.0
    if min_delay >= max_delay:
        print("最小时间间隔必须小于最大时间间隔，使用默认值（2-5秒）")
        min_delay, max_delay = 2.0, 5.0
    if min_delay < 0 or max_delay < 0:
        print("时间间隔不能为负数，使用默认值（2-5秒）")
        min_delay, max_delay = 2.0, 5.0
    delay_times = [
        random.uniform(min_delay, max_delay) for _ in range(len(questions_list))
    ]
    total_time = sum(delay_times)
    print(f"\n已为每个操作生成随机时间间隔（{min_delay:.1f}-{max_delay:.1f}秒）")
    print(f"预计总操作时间: {total_time:.2f}秒 ({total_time / 60:.2f}分钟)")
    match input("确认开始自动提问? [Y/n]: ").upper():
        case "Y" | "":
            pass
        case _:
            return
    for question, delay in zip(questions_list, delay_times):
        try:
            # 确保在正确的页面
            if not check():
                print(f"无法找到问答页面，跳过问题: {question}")
                continue
            WebDriverWait(driver, 2.5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ask-btn"))
            ).click()  # 打开输入框
            WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.TAG_NAME, "textarea"))
            ).send_keys(question)
            check_CAPTCHA()
            time.sleep(2)
            WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".up-btn.ZHIHUISHU_QZMD.set-btn")
                )
            ).click()
            check_CAPTCHA()
            print(f"成功提问: {question}")
            time.sleep(delay)
        except Exception as e:
            print(f"提问失败: {question}")
            print(f"错误信息: {str(e)}")
            print("请检查页面状态，按回车继续下一个问题...")
            input()
            # 尝试切换回问答页面
            check()
            continue


@reloading
def answer():
    if not check():
        return
    course_name = driver.find_element(By.CLASS_NAME, "course-name").text
    print(f"课程名: {course_name}")
    print("鉴于智慧树的屏蔽机制, 建议回答总数量在25个以上 (20个有效回答为有效计分上限)")
    print("请输入本次回答问题序号区间 (索引从0起)")
    start = int(input("From: "))
    end = int(input("To: "))
    if start > end:
        print("请输入正确的区间!")
        return
    replies = end - start + 1
    print(f"\n正在获取页面中第{start}~{end}个问题并发给AI分析, 题目列表如下:")
    question_elements = driver.find_elements(By.CLASS_NAME, "question-content")[
        start : end + 1
    ]
    question_text = ""
    question_title = []
    for question in question_elements:
        print(question.text)
        question_text += question.text + "\n"  # 将所有元素的文本合并
        question_title.append(question.get_attribute("title"))
    ai_question = "请根据提供的问题生成对应的回答, 以下为问题:\n" + question_text
    ai_response = ai_client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "你会收到一些问题, 你要根据问题输出对应的回答, 单个问题的回答需要在一行内不换行输出, 不要带有编号或序号, 输出的问题以换行分隔, 不要使用Markdown或LaTeX语法",
            },
            {"role": "user", "content": ai_question},
        ],
        temperature=0.2,
    )
    answers_list = (
        ai_response.choices[0]
        .message.content.replace("\n\n", "\n")
        .split("\n")[:replies]
    )
    print("\n以下为AI生成的回答:")
    for answer in answers_list:
        print(answer)
    match input("\n开始自动回答? [Y/n]: ").upper():
        case "Y" | "":
            pass
        case _:
            return
    # 获取时间间隔设置
    min_delay_input = input("\n最小时间间隔（不填默认2秒）: ").strip()
    try:
        min_delay = float(min_delay_input) if min_delay_input else 2.0
    except ValueError:
        print("输入无效，使用默认值2秒")
        min_delay = 2.0
    max_delay_input = input("最大时间间隔（不填默认5秒）: ").strip()
    try:
        max_delay = float(max_delay_input) if max_delay_input else 5.0
    except ValueError:
        print("输入无效，使用默认值5秒")
        max_delay = 5.0
    if min_delay >= max_delay:
        print("最小时间间隔必须小于最大时间间隔，使用默认值（2-5秒）")
        min_delay, max_delay = 2.0, 5.0
    if min_delay < 0 or max_delay < 0:
        print("时间间隔不能为负数，使用默认值（2-5秒）")
        min_delay, max_delay = 2.0, 5.0
    delay_times = [
        random.uniform(min_delay, max_delay) for _ in range(len(answers_list))
    ]
    total_time = sum(delay_times)
    print(f"\n已为每个操作生成随机时间间隔（{min_delay:.1f}-{max_delay:.1f}秒）")
    print(f"预计总操作时间: {total_time:.2f}秒 ({total_time / 60:.2f}分钟)")
    match input("确认开始自动回答? [Y/n]: ").upper():
        case "Y" | "":
            pass
        case _:
            return
    ori_page = driver.current_window_handle
    for answer, question, delay in zip(answers_list, question_title, delay_times):
        try:
            # 确保在正确的页面
            if not check():
                print(f"无法找到问答页面，跳过问题: {question}")
                continue
            window_handles_before = driver.window_handles
            driver.find_element(By.XPATH, f'//div[@title="{question}"]').click()
            time.sleep(1)
            window_handles_after = driver.window_handles
            for window in window_handles_after:
                if window not in window_handles_before:
                    new_page = window
            driver.switch_to.window(new_page)
            try:
                WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "my-answer-btn"))
                ).click()  # 打开输入框
            except Exception:
                print(f"本题无法回答, 可能是已经回答过, 题目: {question}")
                driver.close()
                driver.switch_to.window(ori_page)
                continue
            WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.TAG_NAME, "textarea"))
            ).send_keys(answer)
            check_CAPTCHA()
            time.sleep(2)
            WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".up-btn.ZHIHUISHU_QZMD.set-btn")
                )
            ).click()
            check_CAPTCHA()
            print(f"成功回答问题: {question}")
            driver.close()
            driver.switch_to.window(ori_page)
            time.sleep(delay)
        except Exception as e:
            print(f"回答问题失败: {question}")
            print(f"错误信息: {str(e)}")
            # 尝试关闭可能打开的新窗口并切换回原页面
            try:
                if driver.current_window_handle != ori_page:
                    driver.close()
                    driver.switch_to.window(ori_page)
            except Exception:
                pass
            print("请检查页面状态，按回车继续下一个问题...")
            input()
            # 尝试切换回问答页面
            check()
            continue


def main():
    while True:
        print("\n选择模式: [1]提问 [2]回答 [3]退出程序(浏览器也会关闭)")
        mode = input("Input Mode: ")
        match mode:
            case "1":
                ask()
            case "2":
                answer()
            case "3":
                driver.quit()
                return
            case _:
                print("请输入正确的选项")


if __name__ == "__main__":
    main()
