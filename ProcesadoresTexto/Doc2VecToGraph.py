from Doc2Vec import Doc2Vec
import networkx as nx


if __name__ == '__main__':
	d2v = Doc2Vec()
	#d2v.train("/home/dani/crawler/limpiado.txt", "/home/dani/crawler/train.d2v", method="DM", ides="String")
	d2v.loadModel("/home/dani/crawler/train.d2v")
	DG = nx.DiGraph()
	"""
	print d2v.doc2vec.cum_table
	
	for word in d2v.doc2vec.index2word[:1000]:
		similares = d2v.doc2vec.most_similar(word, topn=10)
		for word_, similarity in similares:
			DG.add_edge(word,word_, weight=similarity)

	"""
	for doc in d2v.doc2vec.docvecs.doctags:
		#print doc
		similares = d2v.doc2vec.docvecs.most_similar(doc, topn=50)
		for doc_, similarity in similares:
			DG.add_edge(doc,doc_, weight=similarity)

	nx.write_gexf(DG, "graph_docs.gexf")