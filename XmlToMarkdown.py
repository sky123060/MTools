from xml.dom.minidom import parse
import os


class XmlToMarkdown:
    """一个xml转markdown的小工具

        解析wordpress导出的xml文件, 并将其中的文章批量转换成markdown文件

    Args
    ----
    file : str
        指定从wordpress导出的xml文件  
    """

    def __init__(self, file: str) -> None:
        self.file = file
    
    def _read_wordpress_xml(self) -> list:
        """解析wordpress导出的xml文件, 返回解析出的数据
        """
        posts = []

        # 解析 wordpress 导出的 xml 文件，并将内容写入字典
        with parse(self.file) as dom:
            elements = dom.documentElement
            items = elements.getElementsByTagName('item')

            for item in items:
                # 只解析 post_type 为 post 节点，即只解析文章，过滤掉附件、菜单等
                if item.getElementsByTagName('wp:post_type')[0].childNodes[0].data == 'post':
                    try:
                        # 单篇文章的内容
                        post = {
                            "title": item.getElementsByTagName('title')[0].childNodes[0].data,
                            "slug": item.getElementsByTagName('wp:post_name')[0].childNodes[0].data,
                            "date": item.getElementsByTagName('wp:post_date')[0].childNodes[0].data,
                            "lastmod": item.getElementsByTagName('wp:post_modified')[0].childNodes[0].data,
                            "content": item.getElementsByTagName('content:encoded')[0].childNodes[0].data,
                            "categories": [],
                            "tags": []
                        }
                        # 分类和标签的 Tag 都是 category, 而且可能有多条，此处做一个循环和判断
                        if item.getElementsByTagName('category'):
                            for cat in item.getElementsByTagName('category'):
                                if cat.getAttribute("domain") == 'category':
                                    post['categories'].append(cat.childNodes[0].data)
                                elif cat.getAttribute("domain") == 'post_tag':
                                    post['tags'].append(cat.childNodes[0].data)
                        # 单篇文章字典追加到文章列表中
                        posts.append(post)
                    except:
                        pass

        print(f"一共解析了{len(posts)}篇文章")
        return posts

    def to_md(self, path: str = None) -> None:
        """将解析出的数据写入markdown文件, 命名为`文章日期+文章名称.md`
        
        输出到指定位置或当前目录下的`output`文件夹中

        Args
        ----
        path : str
            指定输出文件的位置, 不指定默认为当前所在的目录
        """
        data = self._read_wordpress_xml()
        # 不指定 path, 则默认为当前文件所在的目录
        if path:
            path = path + "\\output"
        else:
            path = os.getcwd() + "\\output"

        # 创建 output 文件夹
        if not os.path.exists(path):
            os.mkdir(path)

        for post in data:
            # 定义 markdown 文件名
            filename = f"{post['date'][:10].replace('-', '')}-{post['title']}.md"

            with open(os.path.join(path, filename), encoding='utf-8', mode='a') as f:
                # 根据自己的文章模板构造写入内容
                text = f"""---
title: "{post['title']}"
slug: "{post['slug']}"
date: {post['date'].replace(' ', 'T') + '+08:00'}
lastmod: {post['lastmod'].replace(' ', 'T') + '+08:00'}
keywords: ""
description: ""\n
categories: {str(post['categories']).replace("'", '"')}
tags: {str(post['tags']).replace("'", '"')}
featuredImage: ""
toc: false
---\n
{post['content']}"""

                f.write(text)
        print('转换完成！')


if __name__ == '__main__':

    file = 'WordPress.xml'

    tool = XmlToMarkdown(file)
    tool.to_md()
