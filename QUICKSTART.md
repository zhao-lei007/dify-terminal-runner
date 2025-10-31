# 快速开始指南 - Dify Terminal Runner Plugin

## 🚀 3分钟快速上手

### 步骤 1: 本地测试（无需 Docker）

```bash
# 进入插件目录
cd /Users/zhaolei/Downloads/github/dify_plugin/terminal_run

# 运行基础测试
python3 test_basic.py
```

**预期输出:**
```
✅ All basic tests passed!
```

### 步骤 2: 在 Python 代码中使用

创建测试文件 `my_test.py`:

```python
from main import run

# 执行简单代码
result = run(
    code="print('Hello, Dify!')",
    session_id="my_session"
)

print(f"成功: {result['success']}")
print(f"输出: {result['output']}")
```

运行:
```bash
python3 my_test.py
```

### 步骤 3: 在 Dify 工作流中使用

#### 方法 A: 本地开发模式

1. 复制插件到 Dify 插件目录：
```bash
cp -r terminal_run /path/to/dify/plugins/
```

2. 在 Dify 工作流中添加 "Terminal Runner" 节点

3. 配置节点：
   - **输入**:
     - `code`: Python 代码（可以是变量引用）
     - `session_id`: 会话ID（可以使用 `{{workflow.run_id}}`）

   - **输出**: 使用 `{{terminal_runner.output}}` 获取执行结果

#### 方法 B: 打包安装

```bash
# 使用 Dify CLI 打包
cd /Users/zhaolei/Downloads/github/dify_plugin
./dify plugin package ./terminal_run

# 生成 terminal_runner-0.2.0.difypkg
# 在 Dify 控制台上传此文件
```

## 📊 示例工作流

### 示例 1: 数据分析流程

```yaml
工作流:
  节点1 [用户输入]:
    - 用户问题: "分析销售数据"

  节点2 [LLM]:
    - Prompt: "根据用户问题生成 Pandas 数据分析代码"
    - 输出: generated_code

  节点3 [Terminal Runner]:
    - code: {{节点2.generated_code}}
    - session_id: {{workflow.run_id}}
    - 输出: result

  节点4 [条件分支]:
    - IF {{节点3.success}} == true:
        → 显示结果: {{节点3.output}}
    - ELSE:
        → 显示错误: {{节点3.error_message}}
```

### 示例 2: 多轮代码执行

```yaml
场景: 用户分步骤执行数据处理

第一轮 - 加载数据:
  Terminal Runner:
    code: |
      import pandas as pd
      data = pd.read_csv('data.csv')
      data.to_pickle('data.pkl')
      print(f'Loaded {len(data)} rows')
    session_id: "user_{{user_id}}_analysis"

第二轮 - 数据处理 (同一 session):
  Terminal Runner:
    code: |
      import pandas as pd
      data = pd.read_pickle('data.pkl')
      processed = data.groupby('category').sum()
      print(processed)
    session_id: "user_{{user_id}}_analysis"  # 相同 session_id
```

## 🔧 常见代码示例

### 1. 数据计算

```python
from main import run

code = """
import pandas as pd
import numpy as np

data = {
    'sales': [100, 200, 150, 300],
    'costs': [50, 100, 75, 150]
}

df = pd.DataFrame(data)
df['profit'] = df['sales'] - df['costs']

print(f"总利润: {df['profit'].sum()}")
print(f"平均利润: {df['profit'].mean():.2f}")
"""

result = run(code=code, session_id="calc_001")
print(result['output'])
```

### 2. 生成图表

```python
code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('Sine Wave')
plt.savefig('chart.png')
print('Chart saved to chart.png')
"""

result = run(code=code, session_id="plot_001")
print(f"生成的文件: {result['artifact_files']}")
```

### 3. API 调用

```python
code = """
import requests

response = requests.get('https://api.github.com/users/github')
data = response.json()

print(f"Name: {data['name']}")
print(f"Repos: {data['public_repos']}")
"""

result = run(code=code, session_id="api_001")
print(result['output'])
```

## 🐳 Docker 部署（可选）

```bash
# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 进入容器测试
docker-compose exec terminal-runner python3 test_basic.py
```

## 📝 输出字段说明

| 字段 | 类型 | 说明 | 使用场景 |
|------|------|------|----------|
| `success` | bool | 是否成功执行 | 条件分支判断 |
| `output` | string | 主要输出内容 | 显示给用户 |
| `has_error` | bool | 是否有错误 | 错误处理分支 |
| `error_message` | string | 错误消息 | 显示错误信息 |
| `has_artifacts` | bool | 是否生成文件 | 文件下载分支 |
| `artifact_files` | list | 文件列表 | 列出生成的文件 |
| `execution_time` | float | 执行时间(秒) | 性能监控 |

## 🆘 故障排查

### 问题 1: 模块导入错误

```bash
# 安装缺失的库
pip3 install pandas numpy matplotlib
```

### 问题 2: 路径权限问题

```bash
# 创建 sessions 目录
mkdir -p sessions
chmod 755 sessions
```

### 问题 3: Session 数据找不到

确保：
1. 使用相同的 `session_id`
2. 使用相对路径读写文件
3. 文件名正确

```python
# 正确 ✅
with open('data.json', 'w') as f:
    ...

# 错误 ❌
with open('/tmp/data.json', 'w') as f:
    ...
```

## 📚 下一步

- 阅读完整文档: [README.md](README.md)
- 查看更多示例: 运行 `python3 main.py`
- 集成到 Dify: 参考 [README.md#dify-集成](README.md#dify-集成)

## 💡 技巧

1. **会话管理**: 使用有意义的 session_id，如 `user_{user_id}_{task_type}`
2. **错误处理**: 始终检查 `success` 字段并处理错误
3. **文件持久化**: 同一 session_id 可以跨多次调用共享数据
4. **性能优化**: 监控 `execution_time` 字段

---

**Happy Coding! 🎉**
