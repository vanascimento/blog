from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import  PromptTemplate
from langchain.chains.question_answering import  load_qa_chain
from pydantic import BaseModel,Field
from typing import  Literal
from dotenv import load_dotenv

file_path = "./files/enel1.pdf"
loader = PyPDFLoader(file_path)
documents =loader.load()
    

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


prompt = PromptTemplate(
    template="""
                A resposta deve conter exclusivamente a informação em JSON, sem nenhum texto adicional.
                A resposta deve ser no formato e somente com os campos abaixo: \n
                {format_instructions}
                O texto da fatura é o seguinte: \n
                {context}
    """,
    input_variables=["context"],
    partial_variables={
        "format_instructions": output_parser.get_format_instructions()
    }
)

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo")

qa_chain = load_qa_chain(llm=llm,chain_type="stuff",prompt=prompt,verbose=False)
response = qa_chain.run(input_documents=documents,question="Extraia as informações requisitadas da fatura de energia",output_parser=output_parser)

parsed_response = output_parser.parse(response)
print(parsed_response)