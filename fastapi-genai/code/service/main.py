from fastapi import FastAPI, UploadFile
from langchain.schema import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains.question_answering import  load_qa_chain
from langchain.schema import Document
from langchain_core.prompts import  PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel,Field
from typing import  Literal
from dotenv import load_dotenv
load_dotenv()
import fitz

app = FastAPI(
    title="Energy Bill Data",
    summary="API para leitura de dados de conta de energia",
    version="1.0.0",
    contact={
        "github":"https://github.com/vanascimento"
    }
)

    
@app.post("/",description="Arquivo PDF da conta de energia",tags=["Energy Bill Data"])
async def analyze_document_data(file: UploadFile):
    file_content = await file.read()
    document = build_langchain_documents_from_bytes(file_content)

    output_parser = JsonOutputParser(pydantic_object=EnergyCompanyResponse)
    prompt = get_prompt(parser=output_parser)
    
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    
    
    qa_chain = load_qa_chain(llm=llm,chain_type="stuff",prompt=prompt,verbose=False)
    response = qa_chain.run(input_documents=[document])
    json_response = output_parser.parse(response)
    return json_response



def build_langchain_documents_from_bytes(file:bytes):
    text = ""

    with fitz.open(stream=file, filetype="pdf") as doc:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text += page.get_text()
    document = Document(page_content=text)
    return document


def get_prompt(parser:JsonOutputParser):
    prompt = PromptTemplate(
       template="""
                A resposta deve conter exclusivamente a informação em JSON, sem nenhum texto adicional.
                A resposta deve ser no formato: \n
                {format_instructions}
                O texto da fatura é o seguinte: \n
                {context}
    """,
        input_variables=["context"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )
    return prompt

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
    