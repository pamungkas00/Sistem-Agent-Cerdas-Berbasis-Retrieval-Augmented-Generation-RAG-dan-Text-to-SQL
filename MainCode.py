import streamlit as st
import os
from operator import itemgetter

# --- Impor Semua Komponen LangChain & Ollama ---
from langchain_ollama import ChatOllama 
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain 
from langchain.chains.combine_documents import create_stuff_documents_chain 
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage




# FUNGSI SETUP UTAMA DENGAN CACHING
@st.cache_resource
def setup_agent():
    print("======================================================================")
    print("MENJALANKAN PROSES SETUP BERAT (HANYA AKAN MUNCUL SEKALI PER SESI)...")
    print("======================================================================")

    # --- 1. INISIALISASI KOMPONEN DASAR ---
    llm = ChatOllama(model="llama3", temperature=0.2) 
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Koneksi ke Database MySQL lokal
    db_uri = "mysql+pymysql://root:admin@127.0.0.1:3306/ai_pelanggan"
    db = SQLDatabase.from_uri(
        db_uri,
        include_tables=['gangguan_', 'pelanggan_', 'perangkat_', 'status_'], 
        sample_rows_in_table_info=3
    )
    
    # --- 2. LOGIKA VECTOR STORE (KNOWLEDGE BASE) ---
    persist_directory = "./chroma_db"
    if os.path.exists(persist_directory):
        print("Memuat vector store ChromaDB yang sudah ada...")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    else:
        print("Vector store tidak ditemukan. Membuat baru dari dokumen...")
        
        loader1 = WebBaseLoader('https://dte.telkomuniversity.ac.id/fiber-to-the-home-ftth/')
        loader2 = PyPDFLoader("D:/AI data Pelanggan/Kurose-7.pdf")
        loader3 = PyPDFLoader("D:/AI data Pelanggan/Modul 2 - Fiber Optic Fundamental[1].pdf")
        loader4 = PyPDFLoader("D:/AI data Pelanggan/Modul 1 - Basic Internet & Infra ICON+.pdf")
        loader5 = PyPDFLoader("D:/AI data Pelanggan/Modul 3 - Instalasi Fiber Optic.pdf")
        loader6 = PyPDFLoader("D:/AI data Pelanggan/RINGKASAN MODUL 1-3.pdf")

        docs1, docs2, docs3, docs4, docs5, docs6 = loader1.load(), loader2.load(), loader3.load(), loader4.load(), loader5.load(), loader6.load()
        all_docs = docs1 + docs2 + docs3 + docs4 + docs5 + docs6
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        splits = text_splitter.split_documents(all_docs)

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory
        )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    # --- 3. PERAKITAN PIPELINE KEMAMPUAN (CHAINS) ---
    
    # Jalur A: RAG Chain
    rag_prompt_template = """Anda adalah asisten ahli teknis jaringan. Jawab pertanyaan berikut dalam Bahasa Indonesia berdasarkan konteks dokumen yang diberikan.
    Konteks: {context}
    Pertanyaan: {input}
    Jawaban:"""
    rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)
    document_chain = create_stuff_documents_chain(llm, rag_prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)

    # Jalur B: Rantai Kustom Text-to-SQL (LCEL)
    sql_query_template = """Berdasarkan skema tabel di bawah, tulis kueri SQL MySQL murni untuk menjawab pertanyaan pengguna.
    Hanya kembalikan kueri SQL dan TIDAK BOLEH ADA YANG LAIN!!. Jangan gunakan karakter backticks (`) pada nama kolom atau tabel.

    Skema Tabel:
    {schema}

    Pertanyaan: {question}
    Kueri SQL:"""
    sql_query_prompt = ChatPromptTemplate.from_template(sql_query_template)

    sql_query_chain = (
        RunnablePassthrough.assign(schema=lambda x: db.get_table_info())
        | sql_query_prompt
        | llm.bind(stop=["\nObservation:", "\n\n"])
        | StrOutputParser()
    )

    final_answer_template = """Anda adalah analis data pelanggan. Berdasarkan pertanyaan, kueri SQL, dan hasil database berikut, berikan jawaban akhir yang ramah, ringkas, dan lengkap dalam Bahasa Indonesia.
    Pertanyaan: {question}
    Kueri SQL: {query}
    Hasil Kueri: {result}
    Jawaban Akhir:"""
    final_answer_prompt = ChatPromptTemplate.from_template(final_answer_template)

    sql_full_chain = (
        RunnablePassthrough.assign(query=sql_query_chain)
        .assign(result=itemgetter("query") | RunnableLambda(db.run))
        | final_answer_prompt
        | llm
        | StrOutputParser()
    )

    # Jalur C: Chat Umum (General Casual Chat)
    general_prompt = ChatPromptTemplate.from_template("Anda adalah AMAR-I, asisten AI yang ramah. Jawab sapaan atau pertanyaan umum berikut dalam Bahasa Indonesia: {input}")
    general_chain = general_prompt | llm | StrOutputParser()

    # Jalur D: PENGELOLA RUTE DINAMIS (LCEL Router)
    router_template = """Analisis pertanyaan pengguna di bawah ini dan tentukan kategori tindakan yang paling tepat.
    Aturan Klasifikasi:
    - Ketik 'SQL' jika pertanyaan memerlukan pencarian data spesifik, jumlah angka, status tiket aktif, alamat, atau informasi tabel database pelanggan.
    - Ketik 'RAG' jika pertanyaan menanyakan tentang teori, konsep, prosedur, SOP perbaikan, atau penjelasan teknis perangkat keras/jaringan berdasarkan dokumen.
    - Ketik 'GENERAL' jika pertanyaan hanya berupa sapaan casual, salam, atau obrolan umum di luar topik data dan dokumen teknis.

    Tanggapi HANYA dengan satu kata antara 'SQL', 'RAG', atau 'GENERAL'. Jangan beri penjelasan atau tanda baca apa pun!

    Pertanyaan: {input}
    Kategori:"""
    router_prompt = ChatPromptTemplate.from_template(router_template)
    router_chain = router_prompt | llm | StrOutputParser()
    
    print("======================================================================")
    print("SETUP SELESAI. APLIKASI SIAP DENGAN MODE LOGGING & STREAMING.")
    print("======================================================================")
    
    return {
        "router": router_chain,
        "rag": rag_chain,
        "sql": sql_full_chain,
        "general": general_chain
    }


# ==============================================================================
# BAGIAN ANTARMUKA GRAFIS USER (STREAMLIT UI)
# ==============================================================================

st.set_page_config(page_title="AMAR-I", page_icon="🤖")
st.title("🤖 AMAR-I")
st.caption("Hai AmartaVengers!")

# Memanggil inisialisasi komponen rantai pintar
chains = setup_agent()

# Inisialisasi status memori chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Merender riwayat percakapan sebelumnya ke layar web
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Menerima input kueri baru dari user
if prompt := st.chat_input("Ajukan pertanyaan Anda di sini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Tempat penampung teks dinamis (Streaming Box)
        placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Menganalisis intensi kueri..."):
            # 1. IMPLEMENTASI SLIDING WINDOW MEMORY
            context_history = st.session_state.messages[-6:] if len(st.session_state.messages) > 6 else st.session_state.messages
            chat_history = []
            for msg in context_history[:-1]:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # 2. EKSEKUSI ROUTING (Penentuan Jalur)
            decision = chains["router"].invoke({"input": prompt}).strip().upper()
            
            # --- PENAMBAHAN PRINT LOG KUSTOM UNTUK MATERI LAPORAN ---
            print("\n" + "="*60)
            print(f"[PENGUJIAN SISTEM AMAR-I] PERTANYAAN USER : {prompt}")
            print(f"[PENGUJIAN SISTEM AMAR-I] LOGIKA ROUTING  : DIALIKAN KE -> {decision}")
            print("="*60 + "\n")
            
        try:
            # 3. IMPLEMENTASI EFEK TEKS MENGALIR (STREAMING TOKENS)
            if "SQL" in decision:
                # Menjalankan stream pada rantai kustom SQL
                for chunk in chains["sql"].stream({"question": prompt, "chat_history": chat_history}):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌") # Menambahkan kursor ketik dinamis
                    
            elif "RAG" in decision:
                # Menjalankan stream pada rantai dokumen RAG
                for chunk in chains["rag"].stream({"input": prompt, "chat_history": chat_history}):
                    if "answer" in chunk:
                        full_response += chunk["answer"]
                        placeholder.markdown(full_response + "▌")
            else:
                # Menjalankan stream pada obrolan santai biasa
                for chunk in chains["general"].stream({"input": prompt, "chat_history": chat_history}):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
            
            # Menghapus kursor pengetikan saat token teks sudah selesai dikirim seluruhnya
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_message = f"Terjadi kesalahan pemrosesan data: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
