from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
# from langchain.chat_models import ChatOpenAI #直接访问OpenAI的GPT服务

#llm = ChatOpenAI(model_name="gpt-4", temperature=0) #直接访问OpenAI的GPT服务
llm = AzureChatOpenAI(deployment_name = deployment, model_name=model, temperature=0.3, max_tokens=1000) #通过Azure的OpenAI服务

retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 8})
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever,
                                 return_source_documents=False, verbose=True)

def find_declarations(directory, json_string):
    # Parse the JSON string
    json_data = json.loads(json_string)
    package_name = json_data["package_name"]
    element_name = json_data["element"]
    ret = qa(f"give me the declaration of {element_name} in package {package_name}")
    return ret['result']

#利用向量数据库寻找代码