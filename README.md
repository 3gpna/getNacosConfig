# 背景
针对内网Nacos资产较多情况（划重点），又懒得一个个翻配置文件，所以写了一个脚本，利用Nacos JWT默认key漏洞，将配置文件全部导出，方便查看。

同时，写了一些正则去检测导出的配置文件中，是否存在的敏感信息，解放双眼双手。（可以根据自己的需求，自己加正则）

# 目前支持什么
> 1、存在JWT默认key资产的所有配置文件导出；

> 2、检测配置文件是否存在阿里、腾云、AWS的AK；

> 3、检测配置文件是否存在企微corpid;

# 怎么用
>1.安装
```
git clone https://github.com/3gpna/getNacosConfig.git
cd getNacosConfig
pip3 install -r requirements.txt
```

>2.使用
```
# 同目录放入nacos IP的txt，每行一个，不要带端口号！！！直接放入IP！！！
# 或者直接把你想放的IP都放进去也行，脚本会自己判断
python getNacosConfig_cmd.py -t 8848.txt 
```

>3.结果文件说明
```
results_config.txt文件中是获取到的原始配置文件
详细解释如下：
```
![image](https://github.com/user-attachments/assets/f569ea95-4e59-4fb1-90f3-0d4e72f02246)
![image](https://github.com/user-attachments/assets/5b38bf8f-6f28-4b57-97ec-2e0cb61316f3)
```
results_findsome.txt是根据正则匹配到的敏感信息：
```
![image](https://github.com/user-attachments/assets/7fec1fb9-0de6-49d8-b0ed-9697140444a8)

# 给想要二开的师傅
1、脚本整体逻辑是什么？

先导出Nacos配置文件，然后再利用正则进行分析。
所以如果正则不全/不想写正则的话，也可以直接在导出的配置文件里手动去找敏感信息。

2、如何添加正则？
![image](https://github.com/user-attachments/assets/c304e732-f4fa-45ae-b7ae-5bf210c0c9af)

# 不足

1、对获取到的json格式配置文件没有处理；

2、正则规则不够多，得师傅们自己添加；

3、只能匹配是否有敏感信息，比如results_findsome.txt含有匹配到的AK，则对应的SK要到results_config.txt按图索骥似的查找！
![image](https://github.com/user-attachments/assets/bf2d2466-ebf4-4dae-b3e2-3c669e8c6a47)


