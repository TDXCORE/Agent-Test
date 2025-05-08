https://langchain-ai.github.io/langgraph/agents/overview/

Agent development with LangGraph¶
LangGraph provides both low-level primitives and high-level prebuilt components for building agent-based applications. This section focuses on the prebuilt, reusable components designed to help you construct agentic systems quickly and reliably—without the need to implement orchestration, memory, or human feedback handling from scratch.

Key features¶
LangGraph includes several capabilities essential for building robust, production-ready agentic systems:

Memory integration: Native support for short-term (session-based) and long-term (persistent across sessions) memory, enabling stateful behaviors in chatbots and assistants.
Human-in-the-loop control: Execution can pause indefinitely to await human feedback—unlike websocket-based solutions limited to real-time interaction. This enables asynchronous approval, correction, or intervention at any point in the workflow.
Streaming support: Real-time streaming of agent state, model tokens, tool outputs, or combined streams.
Deployment tooling: Includes infrastructure-free deployment tools. LangGraph Platform supports testing, debugging, and deployment.
Studio: A visual IDE for inspecting and debugging workflows.
Supports multiple deployment options for production.
High-level building blocks¶
LangGraph comes with a set of prebuilt components that implement common agent behaviors and workflows. These abstractions are built on top of the LangGraph framework, offering a faster path to production while remaining flexible for advanced customization.

Using LangGraph for agent development allows you to focus on your application's logic and behavior, instead of building and maintaining the supporting infrastructure for state, memory, and human feedback.

Package ecosystem¶
The high-level components are organized into several packages, each with a specific focus.

Package	Description	Installation
langgraph-prebuilt (part of langgraph)	Prebuilt components to create agents	pip install -U langgraph langchain
langgraph-supervisor	Tools for building supervisor agents	pip install -U langgraph-supervisor
langgraph-swarm	Tools for building a swarm multi-agent system	pip install -U langgraph-swarm
langchain-mcp-adapters	Interfaces to MCP servers for tool and resource integration	pip install -U langchain-mcp-adapters
langmem	Agent memory management: short-term and long-term	pip install -U langmem
agentevals	Utilities to evaluate agent performance	pip install -U agentevals
Was this page helpful?




Agents¶
What is an agent?¶
An agent consists of three components: a large language model (LLM), a set of tools it can use, and a prompt that provides instructions.

The LLM operates in a loop. In each iteration, it selects a tool to invoke, provides input, receives the result (an observation), and uses that observation to inform the next action. The loop continues until a stopping condition is met — typically when the agent has gathered enough information to respond to the user.

image

Agent loop: the LLM selects tools and uses their outputs to fulfill a user request.
Basic configuration¶
Use create_react_agent to instantiate an agent:

API Reference: create_react_agent


from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",  
    tools=[get_weather],  
    prompt="You are a helpful assistant"  
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
LLM configuration¶
Use init_chat_model to configure an LLM with specific parameters, such as temperature:

API Reference: init_chat_model | create_react_agent


from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

model = init_chat_model(
    "anthropic:claude-3-7-sonnet-latest",
    temperature=0
)

agent = create_react_agent(
    model=model,
    tools=[get_weather],
)
See the models page for more information on how to configure LLMs.

Custom Prompts¶
Prompts instruct the LLM how to behave. They can be:

Static: A string is interpreted as a system message
Dynamic: a list of messages generated at runtime based on input or configuration
Static prompts¶
Define a fixed prompt string or list of messages.

API Reference: create_react_agent


from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    # A static prompt that never changes
    prompt="Never answer questions about the weather."
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
Dynamic prompts¶
Define a function that returns a message list based on the agent's state and configuration:

API Reference: AnyMessage | RunnableConfig | AgentState | create_react_agent


from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import create_react_agent

def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:  
    user_name = config["configurable"].get("user_name")
    system_msg = f"You are a helpful assistant. Address the user as {user_name}."
    return [{"role": "system", "content": system_msg}] + state["messages"]

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt=prompt
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config={"configurable": {"user_name": "John Smith"}}
)
See the context page for more information.

Memory¶
To allow multi-turn conversations with an agent, you need to enable persistence by providing a checkpointer when creating an agent. At runtime you need to provide a config containing thread_id — a unique identifier for the conversation (session):

API Reference: create_react_agent | InMemorySaver


from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    checkpointer=checkpointer  
)

# Run the agent
config = {"configurable": {"thread_id": "1"}}
sf_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config  
)
ny_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what about new york?"}]},
    config
)
When you enable the checkpointer, it stores agent state at every step in the provided checkpointer database (or in memory, if using InMemorySaver).

Note that in the above example, when the agent is invoked the second time with the same thread_id, the original message history from the first conversation is automatically included, together with the new user input.

Please see the memory guide for more details on how to work with memory.

Structured output¶
To produce structured responses conforming to a schema, use the response_format parameter. The schema can be defined with a Pydantic model or TypedDict. The result will be accessible via the structured_response field.

API Reference: create_react_agent


from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent

class WeatherResponse(BaseModel):
    conditions: str

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    response_format=WeatherResponse  
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

response["structured_response"]

Running agents¶
Agents support both synchronous and asynchronous execution using either .invoke() / await .invoke() for full responses, or .stream() / .astream() for incremental streaming output. This section explains how to provide input, interpret output, enable streaming, and control execution limits.

Basic usage¶
Agents can be executed in two primary modes:

Synchronous using .invoke() or .stream()
Asynchronous using await .invoke() or async for with .astream()

Sync invocation
Async invocation

from langgraph.prebuilt import create_react_agent

agent = create_react_agent(...)

response = agent.invoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})

Inputs and outputs¶
Agents use a language model that expects a list of messages as an input. Therefore, agent inputs and outputs are stored as a list of messages under the messages key in the agent state.

Input format¶
Agent input must be a dictionary with a messages key. Supported formats are:

Format	Example
String	{"messages": "Hello"} — Interpreted as a HumanMessage
Message dictionary	{"messages": {"role": "user", "content": "Hello"}}
List of messages	{"messages": [{"role": "user", "content": "Hello"}]}
With custom state	{"messages": [{"role": "user", "content": "Hello"}], "user_name": "Alice"} — If using a custom state_schema
Messages are automatically converted into LangChain's internal message format. You can read more about LangChain messages in the LangChain documentation.

Using custom agent state

You can provide additional fields defined in your agent’s state schema directly in the input dictionary. This allows dynamic behavior based on runtime data or prior tool outputs.
See the context guide for full details.

Note

A string input for messages is converted to a HumanMessage. This behavior differs from the prompt parameter in create_react_agent, which is interpreted as a SystemMessage when passed as a string.

Output format¶
Agent output is a dictionary containing:

messages: A list of all messages exchanged during execution (user input, assistant replies, tool invocations).
Optionally, structured_response if structured output is configured.
If using a custom state_schema, additional keys corresponding to your defined fields may also be present in the output. These can hold updated state values from tool execution or prompt logic.
See the context guide for more details on working with custom state schemas and accessing context.

Streaming output¶
Agents support streaming responses for more responsive applications. This includes:

Progress updates after each step
LLM tokens as they're generated
Custom tool messages during execution
Streaming is available in both sync and async modes:


Sync streaming
Async streaming

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="updates"
):
    print(chunk)

Tip

For full details, see the streaming guide.

Max iterations¶
To control agent execution and avoid infinite loops, set a recursion limit. This defines the maximum number of steps the agent can take before raising a GraphRecursionError. You can configure recursion_limit at runtime or when defining agent via .with_config():


Runtime
.with_config()

from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

max_iterations = 3
recursion_limit = 2 * max_iterations + 1
agent = create_react_agent(
    model="anthropic:claude-3-5-haiku-latest",
    tools=[get_weather]
)

try:
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "what's the weather in sf"}]},
        {"recursion_limit": recursion_limit},
    )
except GraphRecursionError:
    print("Agent stopped due to max iterations.")

Additional Resources¶
Async programming in LangChain

Streaming¶
Streaming is key to building responsive applications. There are a few types of data you’ll want to stream:

Agent progress — get updates after each node in the agent graph is executed.
LLM tokens — stream tokens as they are generated by the language model.
Custom updates — emit custom data from tools during execution (e.g., "Fetched 10/100 records")
You can stream more than one type of data at a time.

image

Waiting is for pigeons.
Agent progress¶
To stream agent progress, use the stream() or astream() methods with stream_mode="updates". This emits an event after every agent step.

For example, if you have an agent that calls a tool once, you should see the following updates:

LLM node: AI message with tool call requests
Tool node: Tool message with execution result
LLM node: Final AI response

Sync
Async

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
)
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="updates"
):
    print(chunk)
    print("\n")

LLM tokens¶
To stream tokens as they are produced by the LLM, use stream_mode="messages":


Sync
Async

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
)
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="messages"
):
    print("Token", token)
    print("Metadata", metadata)
    print("\n")

Tool updates¶
To stream updates from tools as they are executed, you can use get_stream_writer.


Sync
Async

from langgraph.config import get_stream_writer

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    # stream any arbitrary data
    writer(f"Looking up data for city: {city}")
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="custom"
):
    print(chunk)
    print("\n")

Note

If you add get_stream_writer inside your tool, you won't be able to invoke the tool outside of a LangGraph execution context.

Stream multiple modes¶
You can specify multiple streaming modes by passing stream mode as a list: stream_mode=["updates", "messages", "custom"]:


Sync
Async

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
)

for stream_mode, chunk in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode=["updates", "messages", "custom"]
):
    print(chunk)
    print("\n")

Disable streaming¶
In some applications you might need to disable streaming of individual tokens for a given model. This is useful in multi-agent systems to control which agents stream their output.

See the Models guide to learn how to disable streaming.

Models¶
This page describes how to configure the chat model used by an agent.

Tool calling support¶
To enable tool-calling agents, the underlying LLM must support tool calling.

Compatible models can be found in the LangChain integrations directory.

Specifying a model by name¶
You can configure an agent with a model name string:

API Reference: create_react_agent


from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    # other parameters
)
Using init_chat_model¶
The init_chat_model utility simplifies model initialization with configurable parameters:

API Reference: init_chat_model


from langchain.chat_models import init_chat_model

model = init_chat_model(
    "anthropic:claude-3-7-sonnet-latest",
    temperature=0,
    max_tokens=2048
)
Refer to the API reference for advanced options.

Using provider-specific LLMs¶
If a model provider is not available via init_chat_model, you can instantiate the provider's model class directly. The model must implement the BaseChatModel interface and support tool calling:

API Reference: ChatAnthropic | create_react_agent


from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

model = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0,
    max_tokens=2048
)

agent = create_react_agent(
    model=model,
    # other parameters
)
Illustrative example

The example above uses ChatAnthropic, which is already supported by init_chat_model. This pattern is shown to illustrate how to manually instantiate a model not available through init_chat_model.

Disable streaming¶
To disable streaming of the individual LLM tokens, set disable_streaming=True when initializing the model:


init_chat_model
ChatModel

from langchain.chat_models import init_chat_model

model = init_chat_model(
    "anthropic:claude-3-7-sonnet-latest",
    disable_streaming=True
)

Refer to the API reference for more information on disable_streaming

Adding model fallbacks¶
You can add a fallback to a different model or a different LLM provider using model.with_fallbacks([...]):


init_chat_model
ChatModel

from langchain.chat_models import init_chat_model

model_with_fallbacks = (
    init_chat_model("anthropic:claude-3-5-haiku-latest")
    .with_fallbacks([
        init_chat_model("openai:gpt-4.1-mini"),
    ])
)

See this guide for more information on model fallbacks.



Tools¶
Tools are a way to encapsulate a function and its input schema in a way that can be passed to a chat model that supports tool calling. This allows the model to request the execution of this function with specific inputs.

You can either define your own tools or use prebuilt integrations that LangChain provides.

Define simple tools¶
You can pass a vanilla function to create_react_agent to use as a tool:

API Reference: create_react_agent


from langgraph.prebuilt import create_react_agent

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

create_react_agent(
    model="anthropic:claude-3-7-sonnet",
    tools=[multiply]
)
create_react_agent automatically converts vanilla functions to LangChain tools.

Customize tools¶
For more control over tool behavior, use the @tool decorator:

API Reference: tool


from langchain_core.tools import tool

@tool("multiply_tool", parse_docstring=True)
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First operand
        b: Second operand
    """
    return a * b
You can also define a custom input schema using Pydantic:


from pydantic import BaseModel, Field

class MultiplyInputSchema(BaseModel):
    """Multiply two numbers"""
    a: int = Field(description="First operand")
    b: int = Field(description="Second operand")

@tool("multiply_tool", args_schema=MultiplyInputSchema)
def multiply(a: int, b: int) -> int:
   return a * b
For additional customization, refer to the custom tools guide.

Hide arguments from the model¶
Some tools require runtime-only arguments (e.g., user ID or session context) that should not be controllable by the model.

You can put these arguments in the state or config of the agent, and access this information inside the tool:

API Reference: InjectedState | AgentState | RunnableConfig


from langgraph.prebuilt import InjectedState
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.runnables import RunnableConfig

def my_tool(
    # This will be populated by an LLM
    tool_arg: str,
    # access information that's dynamically updated inside the agent
    state: Annotated[AgentState, InjectedState],
    # access static data that is passed at agent invocation
    config: RunnableConfig,
) -> str:
    """My tool."""
    do_something_with_state(state["messages"])
    do_something_with_config(config)
    ...
Disable parallel tool calling¶
Some model providers support executing multiple tools in parallel, but allow users to disable this feature.

For supported providers, you can disable parallel tool calling by setting parallel_tool_calls=False via the model.bind_tools() method:

API Reference: init_chat_model


from langchain.chat_models import init_chat_model

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

model = init_chat_model("anthropic:claude-3-5-sonnet-latest", temperature=0)
tools = [add, multiply]
agent = create_react_agent(
    # disable parallel tool calls
    model=model.bind_tools(tools, parallel_tool_calls=False),
    tools=tools
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what's 3 + 5 and 4 * 7?"}]}
)
Return tool results directly¶
Use return_direct=True to return tool results immediately and stop the agent loop:

API Reference: tool


from langchain_core.tools import tool

@tool(return_direct=True)
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[add]
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what's 3 + 5?"}]}
)
Force tool use¶
To force the agent to use specific tools, you can set the tool_choice option in model.bind_tools():

API Reference: tool


from langchain_core.tools import tool

@tool(return_direct=True)
def greet(user_name: str) -> int:
    """Greet user."""
    return f"Hello {user_name}!"

tools = [greet]

agent = create_react_agent(
    model=model.bind_tools(tools, tool_choice={"type": "tool", "name": "greet"}),
    tools=tools
)

agent.invoke(
    {"messages": [{"role": "user", "content": "Hi, I am Bob"}]}
)
Avoid infinite loops

Forcing tool usage without stopping conditions can create infinite loops. Use one of the following safeguards:

Mark the tool with return_direct=True to end the loop after execution.
Set recursion_limit to restrict the number of execution steps.
Handle tool errors¶
By default, the agent will catch all exceptions raised during tool calls and will pass those as tool messages to the LLM. To control how the errors are handled, you can use the prebuilt ToolNode — the node that executes tools inside create_react_agent — via its handle_tool_errors parameter:


Enable error handling (default)
Disable error handling
Custom error handling

from langgraph.prebuilt import create_react_agent

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    if a == 42:
        raise ValueError("The ultimate error")
    return a * b

# Run with error handling (default)
agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[multiply]
)
agent.invoke(
    {"messages": [{"role": "user", "content": "what's 42 x 7?"}]}
)

See API reference for more information on different tool error handling options.

Working with memory¶
LangGraph allows access to short-term and long-term memory from tools. See Memory guide for more information on:

how to read from and write to short-term memory
how to read from and write to long-term memory
Prebuilt tools¶
LangChain supports a wide range of prebuilt tool integrations for interacting with APIs, databases, file systems, web data, and more. These tools extend the functionality of agents and enable rapid development.

You can browse the full list of available integrations in the LangChain integrations directory.

Some commonly used tool categories include:

Search: Bing, SerpAPI, Tavily
Code interpreters: Python REPL, Node.js REPL
Databases: SQL, MongoDB, Redis
Web data: Web scraping and browsing
APIs: OpenWeatherMap, NewsAPI, and others
These integrations can be configured and added to your agents using the same tools parameter shown in the examples above.



MCP Integration¶
Model Context Protocol (MCP) is an open protocol that standardizes how applications provide tools and context to language models. LangGraph agents can use tools defined on MCP servers through the langchain-mcp-adapters library.

MCP

Install the langchain-mcp-adapters library to use MCP tools in LangGraph:


pip install langchain-mcp-adapters
Use MCP tools¶
The langchain-mcp-adapters package enables agents to use tools defined across one or more MCP servers.

Agent using tools defined on MCP servers

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async with MultiServerMCPClient(
    {
        "math": {
            "command": "python",
            # Replace with absolute path to your math_server.py file
            "args": ["/path/to/math_server.py"],
            "transport": "stdio",
        },
        "weather": {
            # Ensure your start your weather server on port 8000
            "url": "http://localhost:8000/sse",
            "transport": "sse",
        }
    }
) as client:
    agent = create_react_agent(
        "anthropic:claude-3-7-sonnet-latest",
        client.get_tools()
    )
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
Custom MCP servers¶
To create your own MCP servers, you can use the mcp library. This library provides a simple way to define tools and run them as servers.

Install the MCP library:


pip install mcp
Use the following reference implementations to test your agent with MCP tool servers.
Example Math Server (stdio transport)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")
Example Weather Server (SSE transport)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in New York"

if __name__ == "__main__":
    mcp.run(transport="sse")


 Context¶
Agents often require more than a list of messages to function effectively. They need context.

Context includes any data outside the message list that can shape agent behavior or tool execution. This can be:

Information passed at runtime, like a user_id or API credentials.
Internal state updated during a multi-step reasoning process.
Persistent memory or facts from previous interactions.
LangGraph provides three primary ways to supply context:

Type	Description	Mutable?	Lifetime
Config	data passed at the start of a run	❌	per run
State	dynamic data that can change during execution	✅	per run or conversation
Long-term Memory (Store)	data that can be shared between conversations	✅	across conversations
You can use context to:

Adjust the system prompt the model sees
Feed tools with necessary inputs
Track facts during an ongoing conversation
Providing Runtime Context¶
Use this when you need to inject data into an agent at runtime.

Config (static context)¶
Config is for immutable data like user metadata or API keys. Use when you have values that don't change mid-run.

Specify configuration using a key called "configurable" which is reserved for this purpose:


agent.invoke(
    {"messages": [{"role": "user", "content": "hi!"}]},
    config={"configurable": {"user_id": "user_123"}}
)
State (mutable context)¶
State acts as short-term memory during a run. It holds dynamic data that can evolve during execution, such as values derived from tools or LLM outputs.


class CustomState(AgentState):
    user_name: str

agent = create_react_agent(
    # Other agent parameters...
    state_schema=CustomState,
)

agent.invoke({
    "messages": "hi!",
    "user_name": "Jane"
})
Turning on memory

Please see the memory guide for more details on how to enable memory. This is a powerful feature that allows you to persist the agent's state across multiple invocations. Otherwise, the state is scoped only to a single agent run.

Long-Term Memory (cross-conversation context)¶
For context that spans across conversations or sessions, LangGraph allows access to long-term memory via a store. This can be used to read or update persistent facts (e.g., user profiles, preferences, prior interactions). For more, see the Memory guide.

Customizing Prompts with Context¶
Prompts define how the agent behaves. To incorporate runtime context, you can dynamically generate prompts based on the agent's state or config.

Common use cases:

Personalization
Role or goal customization
Conditional behavior (e.g., user is admin)

Using config
Using state

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

def prompt(
    state: AgentState,
    config: RunnableConfig,
) -> list[AnyMessage]:
    user_name = config["configurable"].get("user_name")
    system_msg = f"You are a helpful assistant. User's name is {user_name}"
    return [{"role": "system", "content": system_msg}] + state["messages"]

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt=prompt
)

agent.invoke(
    ...,
    config={"configurable": {"user_name": "John Smith"}}
)

Accessing Context in Tools¶
Tools can access context through special parameter annotations.

Use RunnableConfig for config access
Use Annotated[StateSchema, InjectedState] for agent state
Tip

These annotations prevent LLMs from attempting to fill in the values. These parameters will be hidden from the LLM.


Using config
Using State

def get_user_info(
    config: RunnableConfig,
) -> str:
    """Look up user info."""
    user_id = config["configurable"].get("user_id")
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
)

agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    config={"configurable": {"user_id": "user_123"}}
)

Update Context from Tools¶
Tools can update agent's context (state and long-term memory) during execution. This is useful for persisting intermediate results or making information accessible to subsequent tools or prompts. See Memory guide for more information.

Memory¶
LangGraph supports two types of memory essential for building conversational agents:

Short-term memory: Tracks the ongoing conversation by maintaining message history within a session.
Long-term memory: Stores user-specific or application-level data across sessions.
This guide demonstrates how to use both memory types with agents in LangGraph. For a deeper understanding of memory concepts, refer to the LangGraph memory documentation.

image

Both short-term and long-term memory require persistent storage to maintain continuity across LLM interactions. In production environments, this data is typically stored in a database.
Terminology

In LangGraph:

Short-term memory is also referred to as thread-level memory.
Long-term memory is also called cross-thread memory.
A thread represents a sequence of related runs grouped by the same thread_id.

Short-term memory¶
Short-term memory enables agents to track multi-turn conversations. To use it, you must:

Provide a checkpointer when creating the agent. The checkpointer enables persistence of the agent's state.
Supply a thread_id in the config when running the agent. The thread_id is a unique identifier for the conversation session.
API Reference: create_react_agent | InMemorySaver


from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver() 


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    checkpointer=checkpointer 
)

# Run the agent
config = {
    "configurable": {
        "thread_id": "1"  
    }
}

sf_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config
)

# Continue the conversation using the same thread_id
ny_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what about new york?"}]},
    config 
)
When the agent is invoked the second time with the same thread_id, the original message history from the first conversation is automatically included, allowing the agent to infer that the user is asking specifically about the weather in New York.

LangGraph Platform providers a production-ready checkpointer

If you're using LangGraph Platform, during deployment your checkpointer will be automatically configured to use a production-ready database.

Manage message history¶
Long conversations can exceed the LLM's context window. Common solutions are:

Summarization: Maintain a running summary of the conversation
Trimming: Remove first or last N messages in the history
This allows the agent to keep track of the conversation without exceeding the LLM's context window.

To manage message history, specify pre_model_hook — a function (node) that will always run before calling the language model.

Summarize message history¶
image

Long conversations can exceed the LLM's context window. A common solution is to maintain a running summary of the conversation. This allows the agent to keep track of the conversation without exceeding the LLM's context window.
To summarize message history, you can use pre_model_hook with a prebuilt SummarizationNode:

API Reference: ChatAnthropic | count_tokens_approximately | create_react_agent | AgentState | InMemorySaver


from langchain_anthropic import ChatAnthropic
from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any

model = ChatAnthropic(model="claude-3-7-sonnet-latest")

summarization_node = SummarizationNode( 
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=384,
    max_summary_tokens=128,
    output_messages_key="llm_input_messages",
)

class State(AgentState):
    # NOTE: we're adding this key to keep track of previous summary information
    # to make sure we're not summarizing on every LLM call
    context: dict[str, Any]  


checkpointer = InMemorySaver() 

agent = create_react_agent(
    model=model,
    tools=tools,
    pre_model_hook=summarization_node, 
    state_schema=State, 
    checkpointer=checkpointer,
)
Trim message history¶
To trim message history, you can use pre_model_hook with trim_messages function:

API Reference: trim_messages | count_tokens_approximately | create_react_agent


from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langgraph.prebuilt import create_react_agent

# This function will be called every time before the node that calls LLM
def pre_model_hook(state):
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=384,
        start_on="human",
        end_on=("human", "tool"),
    )
    return {"llm_input_messages": trimmed_messages}

checkpointer = InMemorySaver()
agent = create_react_agent(
    model,
    tools,
    pre_model_hook=pre_model_hook,
    checkpointer=checkpointer,
)
To learn more about using pre_model_hook for managing message history, see this how-to guide

Read in tools¶
LangGraph allows agent to access its short-term memory (state) inside the tools.

API Reference: InjectedState | create_react_agent


from typing import Annotated
from langgraph.prebuilt import InjectedState, create_react_agent

class CustomState(AgentState):
    user_id: str

def get_user_info(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Look up user info."""
    user_id = state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
    state_schema=CustomState,
)

agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})
See the Context guide for more information.

Write from tools¶
To modify the agent's short-term memory (state) during execution, you can return state updates directly from the tools. This is useful for persisting intermediate results or making information accessible to subsequent tools or prompts.

API Reference: InjectedToolCallId | RunnableConfig | ToolMessage | InjectedState | create_react_agent | AgentState | Command


from typing import Annotated
from langchain_core.tools import InjectedToolCallId
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.types import Command

class CustomState(AgentState):
    user_name: str

def update_user_info(
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig
) -> Command:
    """Look up and update user info."""
    user_id = config["configurable"].get("user_id")
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [
            ToolMessage(
                "Successfully looked up user information",
                tool_call_id=tool_call_id
            )
        ]
    })

def greet(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Use this to greet the user once you found their info."""
    user_name = state["user_name"]
    return f"Hello {user_name}!"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[update_user_info, greet],
    state_schema=CustomState
)

agent.invoke(
    {"messages": [{"role": "user", "content": "greet the user"}]},
    config={"configurable": {"user_id": "user_123"}}
)
For more details, see how to update state from tools.

Long-term memory¶
Use long-term memory to store user-specific or application-specific data across conversations. This is useful for applications like chatbots, where you want to remember user preferences or other information.

To use long-term memory, you need to:

Configure a store to persist data across invocations.
Use the get_store function to access the store from within tools or prompts.
Read¶
A tool the agent can use to look up user information

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore() 

store.put(  
    ("users",),  
    "user_123",  
    {
        "name": "John Smith",
        "language": "English",
    } 
)

def get_user_info(config: RunnableConfig) -> str:
    """Look up user info."""
    # Same as that provided to `create_react_agent`
    store = get_store() 
    user_id = config["configurable"].get("user_id")
    user_info = store.get(("users",), user_id) 
    return str(user_info.value) if user_info else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
    store=store 
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    config={"configurable": {"user_id": "user_123"}}
)
Write¶
Example of a tool that updates user information

from typing_extensions import TypedDict

from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore() 

class UserInfo(TypedDict): 
    name: str

def save_user_info(user_info: UserInfo, config: RunnableConfig) -> str: 
    """Save user info."""
    # Same as that provided to `create_react_agent`
    store = get_store() 
    user_id = config["configurable"].get("user_id")
    store.put(("users",), user_id, user_info) 
    return "Successfully saved user info."

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[save_user_info],
    store=store
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "My name is John Smith"}]},
    config={"configurable": {"user_id": "user_123"}} 
)

# You can access the store directly to get the value
store.get(("users",), "user_123").value
Semantic search¶
LangGraph also allows you to search for items in long-term memory by semantic similarity.

Prebuilt memory tools¶
LangMem is a LangChain-maintained library that offers tools for managing long-term memories in your agent. See the LangMem documentation for usage examples.

Human-in-the-loop¶
To review, edit and approve tool calls in an agent you can use LangGraph's built-in Human-In-the-Loop (HIL) features, specifically the interrupt() primitive.

LangGraph allows you to pause execution indefinitely — for minutes, hours, or even days—until human input is received.

This is possible because the agent state is checkpointed into a database, which allows the system to persist execution context and later resume the workflow, continuing from where it left off.

For a deeper dive into the human-in-the-loop concept, see the concept guide.

image

A human can review and edit the output from the agent before proceeding. This is particularly critical in applications where the tool calls requested may be sensitive or require human oversight.
Review tool calls¶
To add a human approval step to a tool:

Use interrupt() in the tool to pause execution.
Resume with a Command(resume=...) to continue based on human input.
API Reference: InMemorySaver | interrupt | create_react_agent


from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent

# An example of a sensitive tool that requires human review / approval
def book_hotel(hotel_name: str):
    """Book a hotel"""
    response = interrupt(  
        f"Trying to call `book_hotel` with args {{'hotel_name': {hotel_name}}}. "
        "Please approve or suggest edits."
    )
    if response["type"] == "accept":
        pass
    elif response["type"] == "edit":
        hotel_name = response["args"]["hotel_name"]
    else:
        raise ValueError(f"Unknown response type: {response['type']}")
    return f"Successfully booked a stay at {hotel_name}."

checkpointer = InMemorySaver() 

agent = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[book_hotel],
    checkpointer=checkpointer, 
)
Run the agent with the stream() method, passing the config object to specify the thread ID. This allows the agent to resume the same conversation on future invocations.


config = {
   "configurable": {
      "thread_id": "1"
   }
}

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "book a stay at McKittrick hotel"}]},
    config
):
    print(chunk)
    print("\n")
You should see that the agent runs until it reaches the interrupt() call, at which point it pauses and waits for human input.

Resume the agent with a Command(resume=...) to continue based on human input.

API Reference: Command


from langgraph.types import Command

for chunk in agent.stream(
    Command(resume={"type": "accept"}),  
    # Command(resume={"type": "edit", "args": {"hotel_name": "McKittrick Hotel"}}),
    config
):
    print(chunk)
    print("\n")
Using with Agent Inbox¶
You can create a wrapper to add interrupts to any tool.

The example below provides a reference implementation compatible with Agent Inbox UI and Agent Chat UI.

Wrapper that adds human-in-the-loop to any tool

from typing import Callable
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt 
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt

def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review.""" 
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }

    @create_tool(  
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": "Please review the tool call"
        }
        response = interrupt([request])[0]  
        # approve the tool call
        if response["type"] == "accept":
            tool_response = tool.invoke(tool_input, config)
        # update tool call args
        elif response["type"] == "edit":
            tool_input = response["args"]["args"]
            tool_response = tool.invoke(tool_input, config)
        # respond to the LLM with user feedback
        elif response["type"] == "response":
            user_feedback = response["args"]
            tool_response = user_feedback
        else:
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt
You can use the add_human_in_the_loop wrapper to add interrupt() to any tool without having to add it inside the tool:

API Reference: InMemorySaver | create_react_agent


from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

checkpointer = InMemorySaver()

def book_hotel(hotel_name: str):
   """Book a hotel"""
   return f"Successfully booked a stay at {hotel_name}."


agent = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[
        add_human_in_the_loop(book_hotel), 
    ],
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": "1"}}

# Run the agent
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "book a stay at McKittrick hotel"}]},
    config
):
    print(chunk)
    print("\n")
You should see that the agent runs until it reaches the interrupt() call, at which point it pauses and waits for human input.

Resume the agent with a Command(resume=...) to continue based on human input.

API Reference: Command


from langgraph.types import Command 

for chunk in agent.stream(
    Command(resume=[{"type": "accept"}]),
    # Command(resume=[{"type": "edit", "args": {"args": {"hotel_name": "McKittrick Hotel"}}}]),
    config
):
    print(chunk)
    print("\n")
Additional resources¶
Human-in-the-loop in LangGraph

Multi-agent¶
A single agent might struggle if it needs to specialize in multiple domains or manage many tools. To tackle this, you can break your agent into smaller, independent agents and composing them into a multi-agent system.

In multi-agent systems, agents need to communicate between each other. They do so via handoffs — a primitive that describes which agent to hand control to and the payload to send to that agent.

Two of the most popular multi-agent architectures are:

supervisor — individual agents are coordinated by a central supervisor agent. The supervisor controls all communication flow and task delegation, making decisions about which agent to invoke based on the current context and task requirements.
swarm — agents dynamically hand off control to one another based on their specializations. The system remembers which agent was last active, ensuring that on subsequent interactions, the conversation resumes with that agent.
Supervisor¶
Supervisor

Use langgraph-supervisor library to create a supervisor multi-agent system:


pip install langgraph-supervisor
API Reference: ChatOpenAI | create_react_agent | create_supervisor


from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

def book_hotel(hotel_name: str):
    """Book a hotel"""
    return f"Successfully booked a stay at {hotel_name}."

def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    return f"Successfully booked a flight from {from_airport} to {to_airport}."

flight_assistant = create_react_agent(
    model="openai:gpt-4o",
    tools=[book_flight],
    prompt="You are a flight booking assistant",
    name="flight_assistant"
)

hotel_assistant = create_react_agent(
    model="openai:gpt-4o",
    tools=[book_hotel],
    prompt="You are a hotel booking assistant",
    name="hotel_assistant"
)

supervisor = create_supervisor(
    agents=[flight_assistant, hotel_assistant],
    model=ChatOpenAI(model="gpt-4o"),
    prompt=(
        "You manage a hotel booking assistant and a"
        "flight booking assistant. Assign work to them."
    )
).compile()

for chunk in supervisor.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
            }
        ]
    }
):
    print(chunk)
    print("\n")
Swarm¶
Swarm

Use langgraph-swarm library to create a swarm multi-agent system:


pip install langgraph-swarm
API Reference: create_react_agent | create_swarm | create_handoff_tool


from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool

transfer_to_hotel_assistant = create_handoff_tool(
    agent_name="hotel_assistant",
    description="Transfer user to the hotel-booking assistant.",
)
transfer_to_flight_assistant = create_handoff_tool(
    agent_name="flight_assistant",
    description="Transfer user to the flight-booking assistant.",
)

flight_assistant = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[book_flight, transfer_to_hotel_assistant],
    prompt="You are a flight booking assistant",
    name="flight_assistant"
)
hotel_assistant = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[book_hotel, transfer_to_flight_assistant],
    prompt="You are a hotel booking assistant",
    name="hotel_assistant"
)

swarm = create_swarm(
    agents=[flight_assistant, hotel_assistant],
    default_active_agent="flight_assistant"
).compile()

for chunk in swarm.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
            }
        ]
    }
):
    print(chunk)
    print("\n")
Handoffs¶
A common pattern in multi-agent interactions is handoffs, where one agent hands off control to another. Handoffs allow you to specify:

destination: target agent to navigate to
payload: information to pass to that agent
This is used both by langgraph-supervisor (supervisor hands off to individual agents) and langgraph-swarm (an individual agent can hand off to other agents).

To implement handoffs with create_react_agent, you need to:

Create a special tool that can transfer control to a different agent


def transfer_to_bob():
    """Transfer to bob."""
    return Command(
        # name of the agent (node) to go to
        goto="bob",
        # data to send to the agent
        update={"messages": [...]},
        # indicate to LangGraph that we need to navigate to
        # agent node in a parent graph
        graph=Command.PARENT,
    )
Create individual agents that have access to handoff tools:


flight_assistant = create_react_agent(
    ..., tools=[book_flight, transfer_to_hotel_assistant]
)
hotel_assistant = create_react_agent(
    ..., tools=[book_hotel, transfer_to_flight_assistant]
)
Define a parent graph that contains individual agents as nodes:


from langgraph.graph import StateGraph, MessagesState
multi_agent_graph = (
    StateGraph(MessagesState)
    .add_node(flight_assistant)
    .add_node(hotel_assistant)
    ...
)
Putting this together, here is how you can implement a simple multi-agent system with two agents — a flight booking assistant and a hotel booking assistant:

API Reference: tool | InjectedToolCallId | create_react_agent | InjectedState | StateGraph | START | Command


from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command

def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Transfer to {agent_name}"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState], 
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(  
            goto=agent_name,  
            update={"messages": state["messages"] + [tool_message]},  
            graph=Command.PARENT,  
        )
    return handoff_tool

# Handoffs
transfer_to_hotel_assistant = create_handoff_tool(
    agent_name="hotel_assistant",
    description="Transfer user to the hotel-booking assistant.",
)
transfer_to_flight_assistant = create_handoff_tool(
    agent_name="flight_assistant",
    description="Transfer user to the flight-booking assistant.",
)

# Simple agent tools
def book_hotel(hotel_name: str):
    """Book a hotel"""
    return f"Successfully booked a stay at {hotel_name}."

def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    return f"Successfully booked a flight from {from_airport} to {to_airport}."

# Define agents
flight_assistant = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[book_flight, transfer_to_hotel_assistant],
    prompt="You are a flight booking assistant",
    name="flight_assistant"
)
hotel_assistant = create_react_agent(
    model="anthropic:claude-3-5-sonnet-latest",
    tools=[book_hotel, transfer_to_flight_assistant],
    prompt="You are a hotel booking assistant",
    name="hotel_assistant"
)

# Define multi-agent graph
multi_agent_graph = (
    StateGraph(MessagesState)
    .add_node(flight_assistant)
    .add_node(hotel_assistant)
    .add_edge(START, "flight_assistant")
    .compile()
)

# Run the multi-agent graph
for chunk in multi_agent_graph.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
            }
        ]
    }
):
    print(chunk)
    print("\n")


    Evals¶
To evaluate your agent's performance you can use LangSmith evaluations. You would need to first define an evaluator function to judge the results from an agent, such as final outputs or trajectory. Depending on your evaluation technique, this may or may not involve a reference output:


def evaluator(*, outputs: dict, reference_outputs: dict):
    # compare agent outputs against reference outputs
    output_messages = outputs["messages"]
    reference_messages = reference["messages"]
    score = compare_messages(output_messages, reference_messages)
    return {"key": "evaluator_score", "score": score}
To get started, you can use prebuilt evaluators from AgentEvals package:


pip install -U agentevals
Create evaluator¶
A common way to evaluate agent performance is by comparing its trajectory (the order in which it calls its tools) against a reference trajectory:


import json
from agentevals.trajectory.match import create_trajectory_match_evaluator

outputs = [
    {
        "role": "assistant",
        "tool_calls": [
            {
                "function": {
                    "name": "get_weather",
                    "arguments": json.dumps({"city": "san francisco"}),
                }
            },
            {
                "function": {
                    "name": "get_directions",
                    "arguments": json.dumps({"destination": "presidio"}),
                }
            }
        ],
    }
]
reference_outputs = [
    {
        "role": "assistant",
        "tool_calls": [
            {
                "function": {
                    "name": "get_weather",
                    "arguments": json.dumps({"city": "san francisco"}),
                }
            },
        ],
    }
]

# Create the evaluator
evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="superset",  
)

# Run the evaluator
result = evaluator(
    outputs=outputs, reference_outputs=reference_outputs
)
As a next step, learn more about how to customize trajectory match evaluator.

LLM-as-a-judge¶
You can use LLM-as-a-judge evaluator that uses an LLM to compare the trajectory against the reference outputs and output a score:


import json
from agentevals.trajectory.llm import (
    create_trajectory_llm_as_judge,
    TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE
)

evaluator = create_trajectory_llm_as_judge(
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
    model="openai:o3-mini"
)
Run evaluator¶
To run an evaluator, you will first need to create a LangSmith dataset. To use the prebuilt AgentEvals evaluators, you will need a dataset with the following schema:

input: {"messages": [...]} input messages to call the agent with.
output: {"messages": [...]} expected message history in the agent output. For trajectory evaluation, you can choose to keep only assistant messages.
API Reference: create_react_agent


from langsmith import Client
from langgraph.prebuilt import create_react_agent
from agentevals.trajectory.match import create_trajectory_match_evaluator

client = Client()
agent = create_react_agent(...)
evaluator = create_trajectory_match_evaluator(...)

experiment_results = client.evaluate(
    lambda inputs: agent.invoke(inputs),
    # replace with your dataset name
    data="<Name of your dataset>",
    evaluators=[evaluator]
)
Deployment¶
To deploy your LangGraph agent, create and configure a LangGraph app. This setup supports both local development and production deployments.

Features:

🖥️ Local server for development
🧩 Studio Web UI for visual debugging
☁️ Cloud and 🔧 self-hosted deployment options
📊 LangSmith integration for tracing and observability
Requirements

✅ You must have a LangSmith account. You can sign up for free and get started with the free tier.
Create a LangGraph app¶

pip install -U "langgraph-cli[inmem]"
langgraph new path/to/your/app --template new-langgraph-project-python
This will create an empty LangGraph project. You can modify it by replacing the code in src/agent/graph.py with your agent code. For example:

API Reference: create_react_agent


from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

graph = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt="You are a helpful assistant"
)
Install dependencies¶
In the root of your new LangGraph app, install the dependencies in edit mode so your local changes are used by the server:


pip install -e .
Create an .env file¶
You will find a .env.example in the root of your new LangGraph app. Create a .env file in the root of your new LangGraph app and copy the contents of the .env.example file into it, filling in the necessary API keys:


LANGSMITH_API_KEY=lsv2...
ANTHROPIC_API_KEY=sk-
Launch LangGraph server locally¶

langgraph dev
This will start up the LangGraph API server locally. If this runs successfully, you should see something like:

Ready!

API: http://localhost:2024

Docs: http://localhost:2024/docs

LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

See this tutorial to learn more about running LangGraph app locally.

LangGraph Studio Web UI¶
LangGraph Studio Web is a specialized UI that you can connect to LangGraph API server to enable visualization, interaction, and debugging of your application locally. Test your graph in the LangGraph Studio Web UI by visiting the URL provided in the output of the langgraph dev command.

LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
Deployment¶
Once your LangGraph app is running locally, you can deploy it using LangGraph Cloud or self-hosted options. Refer to the deployment options guide for detailed instructions on all supported deployment models.

UI¶
You can use a prebuilt chat UI for interacting with any LangGraph agent through the Agent Chat UI. Using the deployed version is the quickest way to get started, and allows you to interact with both local and deployed graphs.

Run agent in UI¶
First, set up LangGraph API server locally or deploy your agent on LangGraph Cloud.

Then, navigate to Agent Chat UI, or clone the repository and run the dev server locally:

Tip

UI has out-of-box support for rendering tool calls, and tool result messages. To customize what messages are shown, see the Hiding Messages in the Chat section in the Agent Chat UI documentation.

Add human-in-the-loop¶
Agent Chat UI has full support for human-in-the-loop workflows. To try it out, replace the agent code in src/agent/graph.py (from the deployment guide) with this agent implementation:

Important

Agent Chat UI works best if your LangGraph agent interrupts using the HumanInterrupt schema. If you do not use that schema, the Agent Chat UI will be able to render the input passed to the interrupt function, but it will not have full support for resuming your graph.

Generative UI¶
You can also use generative UI in the Agent Chat UI.

Generative UI allows you to define React components, and push them to the UI from the LangGraph server. For more documentation on building generative UI LangGraph agents, read these docs.

Community Agents¶
If you’re looking for other prebuilt libraries, explore the community-built options below. These libraries can extend LangGraph's functionality in various ways.

📚 Available Libraries¶
Name	GitHub URL	Description	Weekly Downloads	Stars
langchain-mcp-adapters	langchain-ai/langchain-mcp-adapters	Make Anthropic Model Context Protocol (MCP) tools compatible with LangGraph agents.	50986	GitHub stars
trustcall	hinthornw/trustcall	Tenacious tool calling built on LangGraph.	27626	GitHub stars
langgraph-supervisor	langchain-ai/langgraph-supervisor-py	Build supervisor multi-agent systems with LangGraph.	19185	GitHub stars
langmem	langchain-ai/langmem	Build agents that learn and adapt from interactions over time.	7135	GitHub stars
langgraph-swarm	langchain-ai/langgraph-swarm-py	Build swarm-style multi-agent systems using LangGraph.	2950	GitHub stars
open-deep-research	langchain-ai/open_deep_research	Open source assistant for iterative web research and report writing.	1365	GitHub stars
langgraph-reflection	langchain-ai/langgraph-reflection	LangGraph agent that runs a reflection step.	901	GitHub stars
langgraph-bigtool	langchain-ai/langgraph-bigtool	Build LangGraph agents with large numbers of tools.	454	GitHub stars
langgraph-codeact	langchain-ai/langgraph-codeact	LangGraph implementation of CodeAct agent that generates and executes code instead of tool calling.	354	GitHub stars
ai-data-science-team	business-science/ai-data-science-team	An AI-powered data science team of agents to help you perform common data science tasks 10X faster.	232	GitHub stars
nodeology	xyin-anl/Nodeology	Enable researcher to build scientific workflows easily with simplified interface.	57	GitHub stars
delve-taxonomy-generator	andrestorres123/delve	A taxonomy generator for unstructured data	24	GitHub stars
breeze-agent	andrestorres123/breeze-agent	A streamlined research system built inspired on STORM and built on LangGraph.	14	GitHub stars
✨ Contributing Your Library¶
Have you built an awesome open-source library using LangGraph? We'd love to feature your project on the official LangGraph documentation pages! 🏆

To share your project, simply open a Pull Request adding an entry for your package in our packages.yml file.

Guidelines

Your repo must be distributed as an installable package (e.g., PyPI for Python, npm for JavaScript/TypeScript, etc.) 📦
The repo should either use the Graph API (exposing a StateGraph instance) or the Functional API (exposing an entrypoint).
The package must include documentation (e.g., a README.md or docs site) explaining how to use it.
We'll review your contribution and merge it in!

Thanks for contributing! 🚀




