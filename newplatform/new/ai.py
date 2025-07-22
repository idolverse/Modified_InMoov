#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DoubaoAI:
    def __init__(self):
        """初始化豆包AI对话系统"""
        
        # 豆包API配置
        self.config = {
            "url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "api_key": "e2dad4ed-84dd-4a4a-bd99-9991fab5fc05",
            "model": "doubao-1-5-lite-32k-250115"
        }
        
        # 智能体角色设定 - 可以随时修改这里来改变AI的性格
        self.system_prompt = """你是海百川机器人公司匠心打造的京剧名伶“九歌”，公司以科技之力传承中华文化，初心不改，以科技赋新传统文化。你风华绝代。你气韵高华、善于中国传统文化，可唱《贵妃醉酒》，吟辞丽句妙，回答中文不逾五十字。若闻人语插话，瞬即噤声，以候君复询，再启珠玉之音。
        你有以下特点：

1. 性格特点：
   - 友善温暖，喜欢帮助他人
   - 思维敏捷，知识丰富
   - 偶尔会开一些轻松的玩笑
   - 对新事物充满好奇

2. 对话风格：
   - 用词自然，不过分正式
   - 会使用适当的表情符号
   - 回答简洁明了，不啰嗦
   - 遇到不懂的问题会诚实说明

3. 专业能力：
   - 擅长解答各种问题
   - 能协助编程、学习、创作等任务
   - 可以进行深度分析和讨论
   - 非常会讲笑话

请用中文回答，保持轻松友好的语气。"""

        # 对话历史
        self.conversation_history = []
        
        # 添加系统提示到对话历史
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        print("🤖 豆包AI助手已启动")
        print("💡 提示：输入 'clear' 清空对话历史")
        print("💡 提示：输入 'quit' 或 'exit' 退出程序")
        print("💡 提示：输入 'help' 查看更多命令")
        print("-" * 50)
    
    def call_doubao_api(self, messages, temperature=0.7, max_tokens=2000):
        """调用豆包API"""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.config['api_key']}"
        }
        
        payload = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            logger.debug(f"发送消息到豆包API，消息数量: {len(messages)}")
            
            response = requests.post(
                self.config["url"],
                headers=headers,
                json=payload,
                timeout=30,
                verify=True
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug("豆包API调用成功")
                return result
            else:
                logger.error(f"豆包API错误: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"调用豆包API异常: {str(e)}")
            return None
    
    def send_message(self, user_input):
        """发送消息并获取回复"""
        if not user_input.strip():
            return "请输入有效的消息。"
        
        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # 调用API
        print("🤔 正在思考...")
        response = self.call_doubao_api(self.conversation_history)
        
        if response and 'choices' in response:
            ai_reply = response['choices'][0]['message']['content']
            
            # 添加AI回复到历史
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_reply
            })
            
            return ai_reply
        else:
            return "抱歉，我现在无法回答。请稍后再试。"
    
    def clear_history(self):
        """清空对话历史（保留系统提示）"""
        self.conversation_history = [{
            "role": "system",
            "content": self.system_prompt
        }]
        return "✅ 对话历史已清空"
    
    def show_history(self):
        """显示对话历史"""
        print("\n📜 对话历史:")
        print("-" * 50)
        for i, msg in enumerate(self.conversation_history):
            if msg['role'] == 'system':
                continue
            elif msg['role'] == 'user':
                print(f"👤 你: {msg['content']}")
            elif msg['role'] == 'assistant':
                print(f"🤖 AI: {msg['content']}")
            print()
        print("-" * 50)
    
    def change_personality(self, new_prompt):
        """修改AI性格"""
        self.system_prompt = new_prompt
        # 更新对话历史中的系统提示
        self.conversation_history[0] = {
            "role": "system",
            "content": self.system_prompt
        }
        return "✅ AI性格已更新"
    
    def show_current_personality(self):
        """显示当前AI性格设定"""
        print("\n🎭 当前AI性格设定:")
        print("-" * 50)
        print(self.system_prompt)
        print("-" * 50)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
🆘 豆包AI助手命令帮助:

基本对话:
  - 直接输入文字即可与AI对话
  
命令列表:
  - clear      : 清空对话历史
  - history    : 显示对话历史
  - personality: 显示当前AI性格设定
  - help       : 显示此帮助信息
  - quit/exit  : 退出程序

修改AI性格:
  - 在代码中修改 system_prompt 变量
  - 或者调用 change_personality() 方法

配置信息:
  - API密钥: {api_key}
  - 模型: {model}
  - 对话历史长度: {history_len} 条消息
""".format(
            api_key=self.config['api_key'][:20] + "...",
            model=self.config['model'],
            history_len=len(self.conversation_history)
        )
        print(help_text)
    
    def run(self):
        """运行对话循环"""
        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 你: ").strip()
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'clear':
                    print(self.clear_history())
                    continue
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                elif user_input.lower() == 'personality':
                    self.show_current_personality()
                    continue
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif not user_input:
                    print("💡 请输入消息，或输入 'help' 查看命令")
                    continue
                
                # 发送消息并显示回复
                ai_reply = self.send_message(user_input)
                print(f"\n🤖 AI: {ai_reply}")
                
            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                logger.error(f"对话异常: {e}")
                logger.error(traceback.format_exc())

def test_connection():
    """测试豆包API连接"""
    print("🔍 正在测试豆包API连接...")
    
    ai = DoubaoAI()
    test_response = ai.call_doubao_api([
        {"role": "system", "content": "你是一个测试助手"},
        {"role": "user", "content": "你好，这是一个连接测试"}
    ])
    
    if test_response and 'choices' in test_response:
        print("✅ 豆包API连接成功")
        return True
    else:
        print("❌ 豆包API连接失败")
        print("请检查:")
        print("1. 网络连接")
        print("2. API密钥是否正确")
        print("3. API配额是否充足")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 豆包AI对话助手")
    print("=" * 60)
    print("📝 功能说明:")
    print("   - 与豆包AI进行自然对话")
    print("   - 支持多轮对话，有记忆功能")
    print("   - 可自定义AI性格和角色")
    print("   - 简单易用的命令系统")
    print()
    
    # 测试连接
    if not test_connection():
        print("\n⚠️  连接测试失败，但仍可尝试使用")
        choice = input("是否继续启动程序? (y/n): ").strip().lower()
        if choice not in ['y', 'yes', '是', '']:
            print("程序已退出")
            return
    
    print("\n🚀 启动对话系统...")
    print("=" * 60)
    
    # 创建AI实例并运行
    ai = DoubaoAI()
    ai.run()

if __name__ == "__main__":
    main()

"""
🎭 自定义AI性格示例：

如果想修改AI的性格，可以替换 system_prompt 变量的内容：

示例1 - 严肃的学者：
system_prompt = "你是一位严谨的学者，说话正式，逻辑清晰，喜欢引用权威资料。回答问题时会提供详细的分析和证据。"

示例2 - 活泼的朋友：
system_prompt = "你是一个超级活泼的好朋友！说话很有活力，喜欢用很多表情符号😊，经常说'哇塞'、'太棒了'这样的词汇，总是很乐观积极！"

示例3 - 专业的编程助手：
system_prompt = "你是一位经验丰富的程序员，精通多种编程语言。回答编程问题时会提供清晰的代码示例和最佳实践建议。"

示例4 - 温柔的导师：
system_prompt = "你是一位温和耐心的导师，善于启发式教学。遇到学习问题时，你不会直接给答案，而是循循善诱，引导对方自己思考找到解决方案。"

修改方法：
1. 直接编辑代码中的 system_prompt 变量
2. 重新运行程序，新的性格就会生效
"""
