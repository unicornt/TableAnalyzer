import re

input = """
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.font_manager as fm

# 精确到小数点后两位
x = [round(i, 2) if isinstance(i, float) else i for i in x]
y = [round(i, 2) if isinstance(i, float) else i for i in y]

plt.rcParams['font.family'] = fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()

fig, ax = plt.subplots(figsize=(10, 8))

ax.bar(x, y)

ax.set_xlabel('成绩区间')
ax.set_ylabel('学生人数')
ax.set_title('学生成绩分布柱状图')

ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
ax.yaxis.set_major_locator(MaxNLocator(nbins=6))

plt.tight_layout()
plt.savefig(filename)

"""

def extract_backtick_content(text):
    # 正则表达式：匹配 ``` 和 ``` 之间的内容
    # print(input)
    pattern = r'```python\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        print('错误格式，尝试提取')
        # 提取被 ``` 包裹的内容
        return match.group(1)  # 返回第一个捕获的组，即反引号中的内容
    # 如果没有找到被 ``` 包裹的内容，返回原文本
    pattern2 = r'\[\n(.*?)\]'
    match2 = re.search(pattern2, text, re.DOTALL)
    
    if match2:
        print('错误格式2，尝试提取')
        return match2.group(1)  # 返回第一个捕获的组，即反引号中的内容
    return text
    
print(extract_backtick_content(input))