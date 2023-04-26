# MTools

个人使用的一些小工具，分享给有需要的朋友

## 1. XmlToMarkdown

### 介绍

一个xml转markdown的小工具

解析wordpress导出的xml文件, 并将其中的文章批量转换成markdown文件

```python
from XmlToMarkdown import XmlToMarkdown

file = 'WordPress.2022-07-15.xml'  # 修改为你的xml
tool = XmlToMarkdown(file)

# path 参数指定文件存放位置，不指定时, 默认在当前文件夹下生成output文件夹，存放转后后的markdown文件
tool.to_md()
```

## 2. HugoToTypecho

### 介绍

帮助从 Hugo 迁移到 Typecho

注：原 Hugo 搭配的评论系统为 Artalk

- update_md: 批量更新 markdown 文件中的图片链接
- get_content: 从 markdown 文件中提取文章的要素和内容
- insert_contents: 将文章信息写入 Typecho 数据库
- insert_metas: 将分类、标签信息写入 Typecho 数据库
- insert_relationships: 构建文章、分类、标签之间的关系并写入 Typecho 数据库
- insert_comments: 将评论数据写入 Typecho 数据库
- update_count: 更新文章评论数、分类文章计数、标签文章计数、评论层级
