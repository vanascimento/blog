---
title: "Como Integrar LangChain, FAISS e ReactAgent para Otimizar Busca Textual em LLMs"
datePublished: Sun Nov 10 2024 20:56:00 GMT+0000 (Coordinated Universal Time)
cuid: cm3c2qsef000f09jiet2cbni4
slug: como-integrar-langchain-faiss-e-reactagent-para-otimizar-busca-textual-em-llms
cover: https://cdn.hashnode.com/res/hashnode/image/upload/v1731271881928/8b743364-4904-436d-8b01-038792803e21.png
ogImage: https://cdn.hashnode.com/res/hashnode/image/upload/v1731272116556/a7ce3d6f-aa2f-4668-9690-4b9b938a180d.png

---

Faturas de energia geralmente possuem uma ou duas páginas, o que facilita o processamento. Entretanto, ao lidarmos com documentos maiores, a necessidade de otimizar a consulta se torna mais evidente. Neste contexto, a estratégia de busca vetorial em documentos é uma solução poderosa, permitindo que o modelo se concentre nas seções mais relevantes. Para isso, utilizamos o FAISS, uma ferramenta desenvolvida pelo Facebook, que organiza e filtra o texto em vetores, garantindo que apenas os trechos essenciais sejam enviados ao modelo. A combinação com o Agent React, que introduz uma camada de raciocínio, permite respostas contextualizadas e precisas, tornando essa abordagem extremamente eficiente para documentos extensos.

## [FAISS](https://ai.meta.com/tools/faiss/)

O FAISS (Facebook AI Similarity Search) é uma biblioteca de busca vetorial que permite encontrar vetores semelhantes em grandes conjuntos de dados de maneira rápida e eficiente. Ele utiliza funções de similaridade, como a similaridade do cosseno, para medir a proximidade entre vetores. A similaridade do cosseno calcula o ângulo entre os vetores, identificando o quão semelhantes eles são com base em sua orientação, o que é particularmente útil para dados textuais ou embeddings de alta dimensão. Essas funcionalidades tornam o FAISS uma escolha poderosa para sistemas que exigem correspondência rápida e precisa entre dados, como buscas em documentos, recomendações e análise de similaridade.

## [React Agent](https://python.langchain.com/v0.1/docs/modules/agents/agent_types/react/)

**React Agent** é uma ferramenta do LangChain que combina múltiplos agentes para tomar decisões mais inteligentes ao interagir com modelos de linguagem. Ele aplica uma abordagem de raciocínio, permitindo que o modelo execute tarefas complexas, tomando decisões baseadas em informações extraídas de dados ou interações anteriores, sem precisar de intervenções externas. Além disso, o React Agent consegue integrar e usar ferramentas externas, o que amplia sua capacidade de realizar tarefas como consultas a bancos de dados, APIs e outros sistemas, tornando-o ainda mais poderoso.

E não, ele **não tem nada a ver com o ReactJS**! Enquanto o ReactJS organiza interfaces de usuário, o React Agent organiza **ações e decisões** de agentes, tornando seu trabalho mais eficiente.

## Roadmap

Utilizaremos como base o código desenvolvido no post anterior. Nesta abordagem, enviamos o documento inteiro para o LLM, o que pode resultar em altos custos, já que as tarifas são proporcionais à quantidade de tokens enviados à API do provedor. Para reduzir o número de tokens, começamos transformando o documento em vários segmentos de tamanho fixo e, em seguida, convertemos esses segmentos em vetores multidimensionais usando o FAISS.

Mas surge a pergunta: como o modelo saberá quais trechos do documento enviar? A resposta é simples: utilizamos a capacidade de raciocínio do React Agent, que fará automaticamente uma busca textual nas ferramentas fornecidas e localizará os trechos mais relevantes para responder à pergunta. O mais interessante dessa estratégia é que, se o React Agent não conseguir responder à pergunta com a consulta inicial, ele pode tentar novamente com uma consulta diferente até que todas as questões sejam resolvidas. Essa flexibilidade torna o processo mais eficiente e adaptável.

Nosso roteiro será o seguinte:

1. **Carregar o documento e dividir em "chunks"**: O primeiro passo será carregar o documento e segmentá-lo em partes menores, com cerca de 200 palavras ou tokens, para facilitar a análise e reduzir a quantidade de tokens enviados ao modelo.
    
2. **Criar uma ferramenta para busca de informações**: Em seguida, criaremos uma "tool" (ferramenta) que o modelo utilizará para buscar as informações relevantes nos segmentos do documento.
    
3. **Definir o Prompt para o Agente React**: Elaboraremos o prompt que orientará o Agente React, permitindo que ele saiba como deve buscar e processar as informações de forma eficaz.
    
4. **Preparar o Agente para execução**: Por fim, configuraremos e prepararemos o Agente React para execução, garantindo que ele esteja pronto para realizar as consultas e raciocínios necessários.
    

## Mãos à obra

Certifique-se de que o arquivo .env esteja no diretório do projeto, configurado com sua `OPENAI_API_KEY` válida.

```python
from dotenv import load_dotenv
load_dotenv()
```

Utilize o `PyPDFLoader` para carregar o documento de uma fatura de energia no formato PDF e o `RecursiveCharacterTextSplitter` para dividir o documento em varios trechos de tamanho 200 com 20 de sobreposição.

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

file_path = "./enel1.pdf"
loader = PyPDFLoader(file_path)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,  # Define o limite de tamanho
    chunk_overlap=20  # Define a sobreposição entre *chunks*, se desejado
)
documents = text_splitter.split_documents(documents)
```

Com os documentos subdivididos em mãos, utilize o `FAISS` para criar uma *vector store* e, em seguida, disponibilize a ferramenta `retriever_tool` ao modelo.

```python
from langchain.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool

vector_store = FAISS.from_documents(documents=documents, embedding=OpenAIEmbeddings())
retriever = create_retriever_tool(vector_store.as_retriever(),name="Documento da conta de energia",description="Texto da fatura de energia elétrica do client")
```

O `OutputParser` será o mesmo modelo definido no post anterior. Lembre-se sempre: todas as descrições do modelo de Parser fazem parte integrante do seu prompt, por isso, é essencial ter atenção redobrada ao detalhar as descrições utilizadas.

```python
from pydantic import BaseModel,Field
from typing import  Literal

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
    
from langchain_core.output_parsers import JsonOutputParser
output_parser = JsonOutputParser(pydantic_object=EnergyCompanyResponse)
```

Crie uma instância do LLM ChatOpenAI e forneça o seguinte prompt. Este texto é fundamental para o funcionamento do React Agent, pois garante que o LLM tenha a capacidade de raciocínio necessária

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI()
from langchain_core.prompts import  PromptTemplate
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
```

Defina o Agent e também o AgentExecutor. Utilize o modo `verbose=true` do AgentExecutor para acompanhar os logs de raciocínio do modelo.

```python
from langchain.agents import create_react_agent,AgentExecutor
agent = create_react_agent(llm=llm,prompt=prompt,tools=[retriever])
agent_executor = AgentExecutor(agent=agent,tools=[retriever],verbose=True,handle_parsing_errors=True)
```

Forneça um comando de input para o agent executor e acompanhe o passo a passo da execução do ReAct Agent

```python
result = agent_executor.invoke({
    "input":"Quais os dados da fatura de energia do cliente?"
})
```

Com os parametros fornecidos, meu log de execução do ReAct foi o seguinte:

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1731270911312/4247eab0-cc78-4fc2-b6b5-6c4a351df186.png align="center")

E o resultado final obtido foi:

```json
{
  "periodo_referencia": "05/2023",
  "proxima_leitura": "15/06/2023",
  "vencimento": "29/05/2023",
  "bandeira_tarifaria": "Verde",
  "nome_distribuidora": "ENEL",
  "codigo_cliente": "28374617",
  "codigo_instalacao": "27364518",
  "tipo_fornecimento": "Trifásico",
  "valor_total": 338.45,
  "consumo_kwh": 380.00,
  "client_nome": "VICTOR NASCIMENTO"
}
```

Esta estratégia nos permite reduzir drasticamente o custo de execucao do modelo com documentos grandes além de tornarmos a solução mais robusta utilizando o ReactAgent.

[Código completo](https://github.com/vanascimento/blog/tree/main/genai-faiss-reactagent).