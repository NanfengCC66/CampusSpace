# CampusSpace 校园场地智能预约管理系统

## 项目简介

CampusSpace 是一个基于 Django 3.2 LTS 开发的校园场地智能预约管理系统，提供场地预约、审批流程、智能推荐、冲突检测等功能。

## 功能特性

### 核心功能
- ✅ **场地管理**：楼宇、场地、设备的增删改查
- ✅ **预约管理**：创建、查询、修改、取消预约
- ✅ **审批流程**：多级审批、批量审批、审批历史
- ✅ **冲突检测**：自动检测时间冲突、容量冲突、设备冲突
- ✅ **智能推荐**：根据需求推荐合适的场地
- ✅ **数据导出**：支持导出预约记录到Excel
- ✅ **消息通知**：站内消息推送系统

### 技术特性
- ✅ **RESTful API**：提供完整的API接口
- ✅ **API文档**：Swagger/ReDoc自动生成文档
- ✅ **华为云集成**：支持OBS对象存储
- ✅ **缓存支持**：Redis缓存提升性能
- ✅ **时区支持**：自动处理时区转换

## 技术栈

- **后端框架**：Django 3.2 LTS
- **前端框架**：Bootstrap 5
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **缓存**：Redis
- **API文档**：drf-yasg
- **对象存储**：华为云OBS

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/NanfengCC66/CampusSpace.git
cd CampusSpace
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 创建演示数据

```bash
python create_demo_accounts.py
python generate_data.py
```

### 6. 启动服务器

```bash
python manage.py runserver
```

访问 http://localhost:8000

### 7. 演示账号

- **管理员**：admin / admin123
- **教师**：teacher / teacher123
- **学生**：student / student123

## 项目结构

```
CampusSpace/
├── apps/                   # 应用模块
│   ├── users/             # 用户管理
│   ├── venues/            # 场地管理
│   ├── bookings/          # 预约管理
│   ├── schedules/         # 课表管理
│   ├── maintenance/       # 维护管理
│   └── common/            # 公共模块
├── config/                # 项目配置
├── templates/             # 模板文件
├── static/                # 静态文件
├── docs/                  # 文档
├── requirements.txt       # 依赖列表
└── manage.py             # Django管理脚本
```

## 核心流程

### 预约流程
1. 用户选择场地
2. 填写预约信息
3. 系统自动冲突检测
4. 提交预约申请
5. 管理员审批
6. 预约生效

### 冲突检测
- 时间有效性检测
- 场地容量检测
- 设备要求检测
- 已批准预约冲突
- 用户时间冲突
- 时间间隔要求

## 演示视频

由于项目未部署到公网，请查看演示视频了解系统功能：

[点击查看演示视频](https://github.com/NanfengCC66/CampusSpace/blob/main/演示视频.mp4)

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

- 项目地址：https://github.com/NanfengCC66/CampusSpace
- 问题反馈：https://github.com/NanfengCC66/CampusSpace/issues

---

**华为云码道训练营项目**