import React from 'react';

interface WelcomeScreenProps {
  onExampleClick: (task: string) => void;
}

const EXAMPLES = [
  {
    icon: '🌐',
    title: 'REST API 开发',
    desc: 'FastAPI 用户管理 CRUD',
    task: '实现一个 REST API 用户管理接口，包含 CRUD 操作，使用 FastAPI 框架',
    workflow: 'build',
  },
  {
    icon: '🔍',
    title: '代码审查',
    desc: '质量 + 安全检查',
    task: '审查当前项目的代码质量和安全漏洞',
    workflow: 'review',
  },
  {
    icon: '🐛',
    title: 'Bug 调试',
    desc: '定位并修复问题',
    task: '修复登录页面无法正确跳转的问题',
    workflow: 'debug',
  },
  {
    icon: '🧪',
    title: '测试用例',
    desc: '核心逻辑全覆盖',
    task: '为项目编写单元测试，覆盖核心业务逻辑',
    workflow: 'test',
  },
];

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onExampleClick }) => {
  return (
    <div className="welcome">
      <div className="welcome__icon">⬡</div>
      <div className="welcome__title">Oh My Coder Desktop</div>
      <div className="welcome__sub">AI 多智能体编程助手</div>
      <div className="welcome__hint">输入任务描述，AI 团队将自动协作完成</div>
      
      <div className="welcome__examples">
        <div className="welcome__examples-title">💡 试试这些任务</div>
        <div className="welcome__examples-grid">
          {EXAMPLES.map((ex, idx) => (
            <button
              key={idx}
              className="welcome__example-card"
              onClick={() => onExampleClick(ex.task)}
            >
              <span className="welcome__example-icon">{ex.icon}</span>
              <span className="welcome__example-title">{ex.title}</span>
              <span className="welcome__example-desc">{ex.desc}</span>
            </button>
          ))}
        </div>
      </div>
      
      <div className="welcome__shortcut-hint">
        Press Enter to send · Shift+Enter for newline
      </div>
    </div>
  );
};

export default WelcomeScreen;
