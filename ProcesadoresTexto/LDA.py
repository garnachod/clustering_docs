# -*- coding: utf-8 -*-
from Doc2Vec import LabeledLineSentence
import os
import gensim
import pyLDAvis.gensim
import pyLDAvis

class LDA(object):
	"""docstring for LDA"""
	def __init__(self):
		super(LDA, self).__init__()
		# save_location + dictionary_loc
		self.dictionary_loc = "/textos/dictionary.dict"
		# save_location + corpus_loc
		self.corpus_loc = "/textos/corpus.mm"
		# save_location + model_loc
		self.model_loc = '/model.lda'


	def train(self, input_path, save_location, dimension = 50, epochs = 100, ides="Number"):
		
		if not os.path.exists(save_location):
			os.mkdir(save_location)

		if not os.path.exists(save_location+"/textos"):
			os.mkdir(save_location+"/textos")

		sentences = LabeledLineSentence(input_path, ides)
		texts = [x.words for x in sentences]

		dictionary = gensim.corpora.Dictionary([doc for doc in texts])
		dictionary.compactify()
		dictionary.save(save_location + self.dictionary_loc)

		corpus = [dictionary.doc2bow(doc) for doc in texts]
		gensim.corpora.MmCorpus.serialize(save_location + self.corpus_loc, corpus)
		corpus = gensim.corpora.MmCorpus(save_location + self.corpus_loc)

		print "entrenando"
		lda = gensim.models.ldamulticore.LdaMulticore(corpus=corpus, id2word=dictionary, num_topics=dimension, chunksize=200000, iterations = 1000)

		lda.save(save_location + self.model_loc)

	def toVis(self, save_location):
		if not os.path.exists(save_location):
			raise Exception("Se debe entrenar primero el modelo")

		corpus = gensim.corpora.MmCorpus(save_location + self.corpus_loc)
		dictionary = gensim.corpora.Dictionary.load(save_location + self.dictionary_loc)
		lda = gensim.models.LdaModel.load(save_location + self.model_loc)

		#pyLDAvis.enable_notebook()
		vis_data = pyLDAvis.gensim.prepare(lda, corpus, dictionary)
		print "preparado"
		#pyLDAvis.show(vis_data, ip='0.0.0.0', port=8888, n_retries=50, local=True, open_browser=False)
		pyLDAvis.save_html(vis_data, save_location + "ldaVis.html")


if __name__ == '__main__':
	"""
	TEST
	"""	
	lda = LDA()
	lda.train("/home/dani/crawler/limpiado.txt", "/home/dani/crawler/LDA", ides="Strings", dimension = 25)
	lda.toVis("/home/dani/crawler/LDA")