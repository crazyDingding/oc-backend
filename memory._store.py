def create_or_load_memory(memory_id: str, embedding_fn) -> VectorStoreRetrieverMemory:
    """创建或加载向量记忆数据库"""
    from langchain.vectorstores import FAISS
    import os
    if os.path.exists(f"memory/{memory_id}.faiss"):
        db = FAISS.load_local(f"memory/{memory_id}", embedding_fn)
    else:
        from langchain.docstore import InMemoryDocstore
        from faiss import IndexFlatL2
        db = FAISS(embedding_fn.embed_query, IndexFlatL2(1536), InMemoryDocstore(), {})
    retriever = db.as_retriever(search_kwargs={"k": 5})
    return VectorStoreRetrieverMemory(retriever=retriever, memory_key="memory")