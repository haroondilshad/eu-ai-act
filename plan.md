1) Parse EU AI Act, generate embeddings using LangChain or CrewAI, and store in Pinecone vector DB.
2) Ingest and parse user AI documentation using LangChain or CrewAI, and store extracted elements in MongoDB
3 )Apply pre-defined extraction prompts to parsed user documentation and map results to relevant EU AI Act provisions via semantic retrieval
4) Based on the analysis, apply a simple formula to calculate a confidence score for the user documentation fit with EU Ai Act
5) Use output prompts to generate a curated compliance report and auto-populate the results into a structured Word document template
6) Run the agent end-to-end on the provided sample use case and validate output against benchmark report for accuracy and completeness
7) Upload all code and keys on client's github, pinecone, mongodb instances
8) Provide basic documentation on the flows for future reference