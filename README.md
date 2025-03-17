To run the streamlit app:
1. Install the requirements
python -m spacy download es_core_news_sm
2. uvicorn csvllama2:app --reload
3. streamlit run mixedchat.py

Run similpatternconneciton.py and shotllama2connection.py

Para añadir la ruta del programa de client y server.bat
nano ~/.zshrc

alias client="java -jar -noverify /Users/sofiamorenolasa/Desktop/Documentos_TFG/similPatternTool/similarwave.jar"
alias server="java -jar /Users/sofiamorenolasa/Desktop/Documentos_TFG/similPatternTool/dist/similPatternTool.jar"

Aplica los cambios:
source ~/.zshrc

Luego ya lo puedes llamar con estos nombres:
client
server