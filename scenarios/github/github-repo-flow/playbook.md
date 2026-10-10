# github-repo-flow 路书
> 最后勘路：2026-09-30

## 步骤

1. 【参考】—
   【目的】打开仓库入口，确认落地的仓库名和自述文件原文都在
   【锚点】地址栏输入 https://github.com/facebook/react 后跳转
   【动作】打开网址 https://github.com/facebook/react（会 301 跳到 https://github.com/react/react）
   【到位标志】读页面文本能搜到「React is a JavaScript library for building user interfaces.」，且面包屑处仓库名显示为 react/react
   GitHub 把 facebook/react 组织迁移映射到 react/react，标题和面包屑都以 react/react 呈现，这是预期内的重定向，不是异常。

2. 【参考】—
   【目的】从仓库页进入工单列表
   【锚点】仓库页顶部 Repository 导航栏里的 Issues 链接
   【动作】点击仓库页导航栏里的「Issues」标签（形如「Issues 860」）
   【到位标志】URL 变为 .../issues，页面文本里能看到「Search results」和以 # 编号开头的工单列表，如 #37715、#37714
   按引用点击 Issues 链接后页面结构没有刷新（观察到的仍是仓库页 DOM），改用打开网址直达 issues 列表页，效果一致且更稳。

3. 【参考】—
   【目的】打开列表第一条工单详情，验证详情与列表是同一条
   【锚点】工单列表第一条的标题/编号，如「#37715」
   【动作】点开列表里排在最前面的那条工单（页面文本最先出现的 #编号）
   【到位标志】URL 变为 .../issues/<编号>，页面标题栏「heading」显示「<标题> #<编号>」，与列表页看到的编号一致
   工单标题在列表和详情里可能非常简短（如仅「Bug:」，正文标题留空），这是该工单本身的真实数据，不是加载失败；按详情页 heading 原文取标题即可。
