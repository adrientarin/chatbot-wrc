"""Interface de chat Streamlit : affiche la conversation et la transmet à l'agent.

Lancement : streamlit run src/chatbot_wrc/app.py
"""

import streamlit as st

from chatbot_wrc.application import construire_agent

st.set_page_config(page_title="Chatbot WRC", page_icon="🏁")
st.title("🏁 Chatbot WRC")
st.caption("Pose-moi tes questions sur la saison de WRC !")

# Une session Streamlit = une conversation : rien n'est conservé d'une session à l'autre.
if "agent" not in st.session_state:
    try:
        st.session_state.agent = construire_agent()
    except RuntimeError as erreur:
        st.error(str(erreur))
        st.stop()
    st.session_state.echanges = []

for role, texte in st.session_state.echanges:
    st.chat_message(role).markdown(texte)

if question := st.chat_input("C'est quand le prochain rallye ?"):
    st.chat_message("user").markdown(question)
    with st.chat_message("assistant"), st.spinner("Je regarde ça…"):
        reponse = st.session_state.agent.repondre(question)
        st.markdown(reponse)
    st.session_state.echanges += [("user", question), ("assistant", reponse)]
