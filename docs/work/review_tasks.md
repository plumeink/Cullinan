# Review Tasks（开发者验证清单）

说明：本清单用于开发者逐项验证 AI 生成的文档草稿与示例。每项请在完成后勾选并在必要处补充 commit/hash 或运行输出。

1. 填写源码版本与时间
   - 操作：在 `docs/work/progress_tracker.md` 的“最新时间点”填写执行时间（ISO 8601）与当前 commit hash。
   - 目标：确保目标产出文档头部可标注确切源码版本。

2. 验证 `core_concepts_draft.md` 引用位置
   - 操作：打开 `cullinan/core` 下每个列出的文件，确认关键类/函数名称并将精确行号范围填入 `docs/work/core_concepts_draft.md` 的“源码引用”部分。
   - 路径示例：`G:\pj\Cullinan - 副本 (3)\cullinan\core\registry.py`

3. 运行最小可执行示例（由 AI 生成或开发者补充）
   - 操作：在 Windows PowerShell 中逐条执行示例命令（每行一个命令，禁止使用 `&&` 串联）。
   - 建议流程：
     - 创建虚拟环境：
       powershell
       python -m venv .venv
     - 激活虚拟环境：
       powershell
       .\.venv\Scripts\Activate.ps1
     - 安装依赖（如有 requirements）：
       powershell
       python -m pip install -r requirements.txt
     - 运行示例脚本（示例由 AI 放在 `examples/` 或 `docs/examples.md`）：
       powershell
       python examples\hello_http.py
   - 记录：把示例运行输出复制到 `docs/work/examples_run_output.md`（可选）或提交到 PR。

4. 验证 IoC/DI 场景
   - 操作：使用提供或自写的最小示例验证以下场景：
     - 单例 provider（相同类型多次解析应返回相同实例）
     - 瞬时 provider（每次解析返回新实例）
     - 循环依赖检测（触发并记录异常信息）
   - 参考文件：`cullinan/core/provider.py`, `cullinan/core/scope.py`, `cullinan/core/injection.py`

5. 验证生命周期钩子
   - 操作：创建带生命周期回调（on_start/on_stop 或 init/destroy）的组件，启动框架或显式触发回调，确认回调被调用顺序与异常处理。
   - 参考文件：`cullinan/core/lifecycle.py`, `cullinan/core/lifecycle_enhanced.py`

6. 检查异常信息与日志（无 emoji）
   - 操作：触发常见错误（未注册类型、注入失败）并确认抛出的异常类型和消息在 `cullinan/core/exceptions.py` 中有定义。
   - 要求：文档示例中的日志与错误输出不得包含 emoji。

7. 验证模块扫描与自动注册（可选）
   - 操作：如果使用 `module_scanner.py` 的自动注册功能，运行扫描示例并确认发现与注册的组件列表。
   - 记录：在 `docs/work/review_tasks.md` 下记录扫描输出或疑问。

8. 校验 MkDocs 构建（可选）
   - 操作：在本地尝试构建 MkDocs（建议在开发者机器上执行）：
     powershell
     mkdocs build
   - 记录：如果出现文档链接或路径问题，在 `docs/work/progress_tracker.md` 中记录并回报给 AI。

9. 翻译与 1:1 对齐检查
   - 操作：在生成 `docs/` 的目标产出文档后，确保 `docs/zh/` 的文件一一对应并内容语义一致（AI 可协助初稿，开发者需校验）。

10. 最终复核并关闭条目
    - 操作：所有必检项完成后，在 `docs/work/progress_tracker.md` 中标注相应里程碑为“完成”，并将目标文档从 `docs/work/` 移动到 `docs/`（或复制并开始翻译到 `docs/zh/`）。


备注：如遇到实现与草稿不一致的地方，请在 `docs/work/review_tasks.md` 内添加新的条目，标注文件与具体行号，并把相关代码片段附上以便 AI 修正文档草稿。

