import os
import re
import time
import sqlite3
import pandas as pd


def update_md(files: list, out_path: str) -> None:
    """批量修改markdown图片链接"""

    rule_header = re.compile("---.*?---", re.DOTALL)
    rule_title = re.compile('title: "(.*?)"', re.DOTALL)
    rule_img = re.compile("!\[.*?\]\((.*?)\)")

    for file in files:
        filename = os.path.split(file)[1]
        print(f"正在处理：{filename}")

        with open(file=file, mode='r', encoding='utf-8') as f:
            # 读取md文件
            md = f.read()

            # 提取 front Matter 中的 title
            header = rule_header.findall(md)[0].replace("'", '"')
            title = rule_title.findall(header)[0]
            
            # 提取内容
            content = md.replace(header, "")
            content = re.sub("^\s*", "", content)  # 删除开头的换行符

            # 没有一级标题的添加一级标题
            rule_content_clear = re.compile(f"#\s{title}")
            waitforclear = rule_content_clear.findall(content)
            if waitforclear:
                content = f"\n\n{content}"
            else:
                content = f"\n\n# {title}\n\n{content}"

            # 修改内容中的图片链接
            imgs = rule_img.findall(content)
            if imgs:
                for img in imgs:
                    old_url = f"]({img})"
                    new_url = f'](attachments/{img})'
                    content = content.replace(old_url, new_url)

            text = f"{header}{content}"

            with open(file=os.path.join(out_path, filename), mode="a", encoding="utf-8") as f2:
                f2.write(text)

    print("处理完成！")


def get_content(files: list) -> tuple:
    """获取所有文章的要素"""
    rule_header = re.compile("---.*?---", re.DOTALL)
    rule_title = re.compile('title: "(.*?)"', re.DOTALL)

    posts = []
    categories = []
    tags = []
    for file in files:
        with open(file=file, mode='r', encoding='utf-8') as f:
            # 读取md文件
            md = f.read()

            # 提取 front Matter 中的 title slug created modified
            header = rule_header.findall(md)[0].replace("'", '"')
            title = rule_title.findall(header)[0]
            slug = re.findall('slug: "(.*?)"', header)[0]
            created = int(time.mktime(time.strptime(re.findall('date: (.*?)\+08:00', header)[0].replace("T", " "), "%Y-%m-%d %H:%M:%S")))
            modified = int(time.mktime(time.strptime(re.findall('lastmod: (.*?)\+08:00', header)[0].replace("T", " "), "%Y-%m-%d %H:%M:%S")))
            category = re.findall('categories: \["(.*?)"\]', header)

            tag = []
            if re.findall('tags: \[(.*?)\]', header):
                tag = re.findall('tags: \[(.*?)\]', header)[0].replace('"', "").replace(" ", "").split(",")
            
            # 提取内容，并去除开头的空格
            content = md.replace(header, "")
            content = re.sub("^\s*", "", content)

            # 去除内容中的一级标题
            rule_content_clear = re.compile(f"#\s{title}\s*")
            waitforclear = rule_content_clear.findall(content)
            if waitforclear:
                content = content.replace(waitforclear[0], "")

            text = f"<!--markdown-->{content}"

        if title == "关于":
            post_type = "page"
        else:
            post_type = "post"
        
        post = title, slug, created, modified, text, 0, 1, post_type, 'publish', '1', '1', '1', 0
        
        posts.append(post)
        categories.append(category)
        tags.append(tag)

    print("文章要素获取完成！")

    return posts, categories, tags


def insert_contents(posts: list, db: str):
    """数据库写入文章内容"""
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        sql_contents = """insert into typecho_contents
            (title, slug, created, modified, text, "order", authorId, type, status, allowComment, allowPing, allowFeed, parent) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

        cur.executemany(sql_contents, posts)

    print("文章写入完成！")


def insert_metas(tags: list, db: str):
    """数据库写入文章分类和标签"""
    # name slug type description count order parent
    metas = [
        ("生活", "life", "category", "记录博主生活中点滴，偶尔写点不痛不痒的文字", 0,0,0),
        ("折腾", "coding", "category", "折腾博客的记录、各种新产品、软件的体验评测", 0,1,0),
        ("话题", "topic", "category", "聊聊时事、电影、音乐，游戏，阐述个人观点", 0,2,0),
        ("行摄", "travel", "category", "分享旅行游记攻略，一路风景以及个人摄影作品", 0,3,0)
    ]
    
    ts = set([t for tag in tags for t in tag])
    for t in ts:
        metas.append((t, t.lower(), "tag", "", 0, 0, 0))

    sql = """insert into typecho_metas (name, slug, type, description, count, "order", parent) values(?,?,?,?,?,?,?)"""
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.executemany(sql, metas)
    
    print("分类、标签写入完成！")


def insert_relationships(posts, cats, tags, db):
    """文章id关联分类和标签id, 并写入数据库"""
    sql_cid = "select cid, slug from typecho_contents where type='post';"
    sql_cat = "select mid, slug from typecho_metas where type='category';"
    sql_tag = "select mid, name from typecho_metas where type='tag';"

    with sqlite3.connect(db) as conn:
        dict_cids = pd.read_sql_query(sql_cid, con=conn, index_col="slug").to_dict()['cid']
        dict_cats =pd.read_sql_query(sql_cat, con=conn, index_col="slug").to_dict()['mid']
        dict_tags =pd.read_sql_query(sql_tag, con=conn, index_col="name").to_dict()['mid']

        result = []
        for ps, cs, ts in zip(posts, cats, tags):
            if ps[7] == "post":
                cid = dict_cids[ps[1]]  # 根据 slug 取 cid
                for c in cs:
                    mid = dict_cats[c.lower()]  # 根据 分类的 slug 取 mid
                    result.append((cid, mid))
                if ts:  # 如果有标签
                    for t in ts:
                        mid = dict_tags[t]  # 根据 标签的 slug 取 mid
                        result.append((cid, mid))

        relationships = pd.DataFrame(result, columns=['cid', 'mid'])
        relationships.to_sql("typecho_relationships", con=conn, if_exists="append", index=False)

    print("文章、分类、标签关联关系已更新！")
        

def insert_comments(db_artalk, db):
    """写入评论数据"""
    # 获取文章评论对照关系
    sql_cid = "select cid, slug from typecho_contents;"
    with sqlite3.connect(db) as conn:    
        dict_cids = pd.read_sql_query(sql_cid, con=conn, index_col="slug").to_dict()['cid']

    # 生成待写入的评论数据
    sql_comment = """
        SELECT
            STRFTIME('%s', SUBSTR(t1.created_at, 1, 19)) as 'created',
            t1.content as 'text',
            REPLACE(REPLACE(REPLACE(t1.page_key, 'http://notesth.com/', ''), 'posts/', ''), '/', '')  as 'slug',
            t1.ua as 'agent',
            t1.ip as 'ip',
            t3.name as 'author',
            (CASE WHEN t3.name='修改为你的ID' THEN 1 ELSE 0 END) as 'authorId',
            1 AS 'ownerId',
            'comment' as 'type',
            'approved' as 'status',
            t3.email as 'mail',
            t3.link as 'url',
            STRFTIME('%s', SUBSTR(t2.created_at, 1, 19)) as 'parent'
        from comments t1
        LEFT JOIN comments t2
        ON t1.rid=t2.id
        LEFT JOIN
            (SELECT id, name, email, link FROM users) t3
        ON t1.user_id=t3.id;
    """
    with sqlite3.connect(db_artalk) as conn:
        comments = pd.read_sql_query(sql_comment, con=conn)
        comments['cid'] = comments["slug"].map(dict_cids)
        comments.drop(columns=['slug'], inplace=True)
        # print(comments.head())

    # cols = ['cid', 'created', 'author', 'authorId', 'ownerId', 'mail', 'url', 'ip', 'agent', 'text', 'type', 'status', 'parent']
    # 写入评论数据
    with sqlite3.connect(db) as conn:
        comments.to_sql(name="typecho_comments", con=conn, index=False, if_exists="append")

    print("评论数据写入完成！")


def update_count(db):
    """更新文章计数, 分类计数, 标签计数"""
    with sqlite3.connect(db) as conn:
        sql_update_comment_count = """UPDATE typecho_contents
            SET 
            commentsNum= IFNULL((
            SELECT num FROM (SELECT cid, COUNT(coid) as 'num' FROM typecho_comments GROUP BY cid) t
            WHERE typecho_contents.cid=t.cid), 0);
        """
        sql_update_metas_count = """UPDATE typecho_metas
            SET
            count=IFNULL((
            SELECT num FROM (SELECT mid, COUNT(cid) as 'num' FROM typecho_relationships GROUP BY mid) t
            WHERE typecho_metas.mid = t.mid), 0);
        """
        sql_comment_parent = "SELECT coid, created FROM typecho_comments;"
        sql_update_comments_parent = f"UPDATE typecho_comments SET parent=? where parent=?;"
        sql_update_comments_parent_fillna = f"UPDATE typecho_comments SET parent=0 where parent is null;"

        # 获取评论层级对照关系
        list_coids = pd.read_sql_query(sql_comment_parent, con=conn).values.tolist()

        cur = conn.cursor()

        # 更新typecho_contents commentsNum
        cur.execute(sql_update_comment_count)
        print("评论数更新完成")
        
        # 更新typecho_metas count
        cur.execute(sql_update_metas_count)
        print("分类、标签文章数更新完成")

        # 更新typecho_comments parent
        cur.executemany(sql_update_comments_parent, list_coids)
        cur.execute(sql_update_comments_parent_fillna)
        print("评论层级关系更新完成")

if __name__ == '__main__':

    md_path = r"F:\Website\posts"
    out_path = r"F:\Website\posts_edit"
    db_typecho = r"F:\Website\typehcho_xxxxx.db"
    db_artalk = r"F:\Website\artalk.db"

    # 更新md文件
    files = [os.path.join(md_path, f) for f in os.listdir(md_path)]
    update_md(files, out_path)

    # 获取文章要素
    files = [os.path.join(out_path, f) for f in os.listdir(out_path)]
    posts, cats, tags = get_content(files)

    # 写入文章
    insert_contents(posts, db_typecho)

    # 写入分类、标签
    insert_metas(tags, db_typecho)

    # 写入文章与分类、标签的关系
    insert_relationships(posts, cats, tags, db_typecho)

    # 写入评论数据
    insert_comments(db_artalk, db_typecho)

    # 更新文章数量和评论数量
    update_count(db_typecho)
