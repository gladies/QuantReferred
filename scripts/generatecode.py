from io import StringIO
import sys
from typing import Dict, Optional
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents.tools import Tool
from langchain.llms import OpenAI


class PythonREPL:
    """Simulates a standalone Python REPL."""

    def __init__(self):
        pass        

    def run(self, command: str) -> str:
        command = '\n'.join(line for line in command.split('\n') if not line.startswith('```'))
        """Run command and returns anything printed."""
        # sys.stderr.write("EXECUTING PYTHON CODE:\n---\n" + command + "\n---\n")
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            exec(command, globals())
            sys.stdout = old_stdout
            output = mystdout.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            output = str(e)
        # sys.stderr.write("PYTHON OUTPUT: \"" + output + "\"\n")
        return output
# from langchain.chat_models import ChatOpenAI #直接访问OpenAI的GPT服务

#llm = ChatOpenAI(model_name="gpt-4", temperature=0) #直接访问OpenAI的GPT服务
llm = AzureChatOpenAI(deployment_name = deployment, model_name=model, temperature=0, max_tokens=1000) #通过Azure的OpenAI服务

python_repl = Tool(
        "Python REPL",
        PythonREPL().run,
        """A Python shell. Use this to execute python commands. 
        Input should be a valid python command.
        If you expect output it should be printed out.
        For example: to verify the the following python function
        ---
        def add(a, b):
            return (a+b)
        ---
        we can invoke the tool with the input 
        "
        def add(a, b):
            return (a+b)
        print (add(1,2))
        
        "
        """,
    )
tools = [python_repl]

#封装一个方法， 叫做写代码
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True, handle_parsing_errors=True)

prompt_1 = prompt + f"\n 给出回答前请用以下例子测试生成的函数:\n 函数输入：{src_dir}, {interface_dec}; 函数输出：{expected}"
print(agent.run(prompt_1))