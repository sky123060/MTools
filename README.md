# MTools

个人使用的一些小工具，分享给有需要的朋友

## 1. XmlToMarkdown

### 介绍

一个xml转markdown的小工具

解析wordpress导出的xml文件, 并将其中的文章批量转换成markdown文件

### 使用方法

```python
from XmlToMarkdown import XmlToMarkdown

file = 'WordPress.2022-07-15.xml'  # 修改为你的xml
tool = XmlToMarkdown(file)

# path 参数指定文件存放位置，不指定时, 默认在当前文件夹下生成output文件夹，存放转后后的markdown文件
tool.to_md()
```
