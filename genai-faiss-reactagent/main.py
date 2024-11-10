from dotenv import load_dotenv
    
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from pydantic import BaseModel,Field
from typing import  Literal
from langchain_core.prompts import  PromptTemplate
from langchain.agents import create_react_agent,AgentExecutor

load_dotenv()


file_path = "./enel1.pdf"
loader = PyPDFLoader(file_path)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,  # Define o limite de tamanho
    chunk_overlap=20  # Define a sobreposição entre *chunks*, se desejado
)
documents = text_splitter.split_documents(documents)




vector_store = FAISS.from_documents(documents=documents, embedding=OpenAIEmbeddings())
retriever = create_retriever_tool(vector_store.as_retriever(),name="DOCUMENTO_ENERGIA",description="Documento da fatura de energia elétrica do cliente")




class EnergyCompanyResponse(BaseModel):
    periodo_referencia: str = Field(description="Periodo de referência da fatura no formato MM/YYYY")
    proxima_leitura: str = Field(description="Data da próxima leitura no formato DD/MM/YYYY")
    vencimento: str = Field(description="Data de vencimento da fatura no formato")
    bandeira_tarifaria: Literal['Vermelha','Amarela','Verde'] = Field(description="Bandeira tarifária da fatura")
    nome_distribuidora: str = Field(description="Nome da companhia distribuidora de energia")
    codigo_cliente: str = Field(description="Código do cliente na distribuidora")
    codigo_instalacao: str = Field(description="Código da instalação na distribuidora")
    tipo_fornecimento: Literal['Monofásico','Bifásico','Trifásico'] = Field(description="Tipo de fornecimento de energia")
    valor_total: float = Field(description="Valor total da fatura")
    consumo_kwh: float = Field(description="Consumo em kWh")
    client_nome: str = Field(description="Nome do cliente")
    
output_parser = JsonOutputParser(pydantic_object=EnergyCompanyResponse)
llm = ChatOpenAI()

prompt = PromptTemplate(
    template="""
                Answer the following questions as best you can. 
                Think step by step to find each field of format instructions.
                You have access to the following tools: {tools}
                The final answer should be in the following format: {format_instructions}

                Use the following format:

                Question: the input question you must answer
                Thought: you should always think about what to do
                Action: the action to take, should be one of [{tool_names}]
                Action Input: the input to the action
                Observation: the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
                Thought: I now know the final answer
                Final Answer: the final answer to the original input question
                The final answer should be in the following format: {format_instructions}
                Begin!

                Question: {input}
                Thought:{agent_scratchpad}
    """,
    partial_variables={
        "format_instructions":output_parser.get_format_instructions(),
    }
)

agent = create_react_agent(llm=llm,prompt=prompt,tools=[retriever])
agent_executor = AgentExecutor(agent=agent,tools=[retriever],verbose=True,handle_parsing_errors=True)

result = agent_executor.invoke({
    "input":"Quais os dados da fatura de energia do cliente?"
})

print(result['output'])