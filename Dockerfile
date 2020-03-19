#基于centos镜像
FROM ubuntu:18.04

#维护人的信息
MAINTAINER The Project <1025304567@qq.com>

#更新源
RUN sed -i s:/archive.ubuntu.com:/mirrors.tuna.tsinghua.edu.cn/ubuntu:g /etc/apt/sources.list
RUN cat /etc/apt/sources.list
RUN apt-get clean
RUN apt-get -y update --fix-missing

#安装python软件包
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y --fix-missing
RUN pip3 install flask -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
RUN pip3 install redis -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
RUN pip3 install paho-mqtt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
RUN pip3 install requests -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

#复制emqx安装包至镜像中
ADD emqx-ubuntu18.04-v3.2.7_amd64.deb /emqx-ubuntu18.04-v3.2.7_amd64.deb

#安装emqx
RUN dpkg -i emqx-ubuntu18.04-v3.2.7_amd64.deb

#安装中文语言支持
RUN apt-get install language-pack-zh-hans -y
RUN LANG=zh_CN.utf8
RUN echo 'export LC_ALL=zh_CN.utf8'>>/etc/profile
#RUN source /etc/profile

#复制脚本文件夹包至镜像中
COPY plugin /plugin

#安装redis
COPY redis-4.0.14.tar.gz /redis-4.0.14.tar.gz
RUN ls && tar -zxvf redis-4.0.14.tar.gz

#复制该脚本至镜像中，并修改其权限
ADD run.sh /run.sh

#赋予执行权限
RUN chmod 775 /run.sh

#当启动容器时执行的脚本文件
CMD ["/run.sh"]
