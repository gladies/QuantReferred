import openai
openai.api_key = "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"

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a senior software engineer."},   
        {"role": "user", "content": """
          Design a twitter like system, represent the business domain model with PlantUML script
          """}
    ],
    temperature = 0.2, 
    max_tokens = 500
  )
print(response.choices[0].message.content)

#要求大模型生成一个像twitter一样的system， 让它写PlantUML script，再用一个解析器（plantUML另一个网页）把它生成成图片

# import openai
# response = openai.ChatCompletion.create(
#     engine=deployment, # engine = "deployment_name".
#     messages=[
#         {"role": "system", "content": "You are a senior software engineer."},   
#         {"role": "user", "content": """
#           Design a facebook like system, represent the interactions by UML sequence diagram with PlantUML script
#           """}
#     ],
#     temperature = 0.2, 
#     max_tokens = 500
#   )
# print(response.choices[0].message.content)

#让大模型生成一个时序图，大模型还可以根据这个uml图生成对应的java代码