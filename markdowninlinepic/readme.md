# markdown 图片下载器

这是一个python工程，可以将markdown文件中的所有图片网址替换为已下载图片的路径。

这是一个简单的Python脚本，可以从markdown文件中下载所有的图片，并用本地路径替换图片的网址。

## 使用方法

要使用这个脚本，你需要在你的系统上安装Python 3。你还需要使用pip安装requests库：

```bash
pip install requests pillow
```

然后，你可以在命令行中运行脚本，传递markdown文件的路径作为参数：

```bash
python main.py -f example.md
```
传递markdown文件夹作为参数：
```bash
python main.py -d examplefolder
```
指定host下载(图片url含有localhost，127.0.0.1时):
```bash
python main.py --host example.com
```
脚本会在markdown文件所在的目录下创建一个名为`images`的文件夹，并把所有下载的图片保存在那里。它还会创建一个新的markdown文件，名为`example_new.md`，其中包含了更新后的图片路径。

## 示例

这是一个在运行脚本之前和之后的markdown文件的例子：

之前：

```markdown
# 我的Markdown文件

这是一个带有一些图片的markdown文件。

![图片1](https://example.com/image1.jpg)

![图片2](https://example.com/image2.png)
```

之后：

```markdown
# 我的Markdown文件

这是一个带有一些图片的markdown文件。

![图片1](images/image1.jpg)

![图片2](images/image2.png)
```

Source: Conversation with Bing, 4/7/2023
(1) GitHub - dephraiim/translate-readme: Translate Github Readme to any .... https://github.com/dephraiim/translate-readme.
(2) . https://bing.com/search?q=translate+readme.md+to+Chinese.
(3) Google Translate. https://translate.google.co.uk/.
