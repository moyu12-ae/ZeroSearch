# ADR-002: Camoufox 集成方式 — Git Submodule

## 状态
**Accepted**

## 背景
Camoufox 需要在项目中可用。有两种集成方式：A) PyPI 安装 (`pip install camoufox`)，B) Git Submodule 直接引用源码。选择影响维护工作流和版本控制。

## 决策
**选择 Git Submodule** (`git submodule add https://github.com/daijro/camoufox.git libs/camoufox`)，配合 `pip install -e libs/camoufox` 使 Python 可 import。

## 候选方案对比

| 维度 | A: PyPI | B: Git Submodule |
|------|:--:|:--:|
| 上游追踪 | 依赖 PyPI 发布节奏，滞后 | `git submodule update --remote` 即时同步 |
| 版本锁定 | pip freeze / requirements.txt | submodule commit hash 精确锁定 |
| 离线可用 | 需 pip install | clone 即含完整源码 |
| 调试便利 | site-packages 中，不便修改 | `libs/camoufox/` 可直接查看/调试源码 |
| clone 复杂度 | 简单 | 需 `--recurse-submodules` |
| breaking change 恢复 | 降级 pip 版本 | `git checkout` 回退 submodule commit |

## 权衡点
- **Submodule 增加 clone 步骤**，但换来精确版本锁定和即时上游更新
- PyPI 安装更简单，但失去对上游 commit 级别的控制

## 后果
### 正面
- 精确控制 Camoufox 版本（commit hash 锁定）
- 上游 bug 修复即时可用
- 可直接调试 Camoufox 源码

### 负面
- 新开发者需了解 `git submodule update --init`
- CI/CD 需配置 `submodules: recursive`

### 后续行动
- 根目录创建 `.gitmodules`
- `pip install -e libs/camoufox` 加入 setup.sh
- AGENTS.md 记录 submodule 更新流程

## 影响范围
- **项目根**: `.gitmodules`, `libs/camoufox/`
- **BrowserEngine**: `import camoufox` 路径
- **setup.sh**: 添加 submodule init + pip install -e
