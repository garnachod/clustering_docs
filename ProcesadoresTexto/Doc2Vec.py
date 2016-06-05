# gensim modules
from gensim import utils, matutils
from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import LabeledSentence
from gensim.models import Doc2Vec
from blist import blist
import gensim
import random
import time
import codecs
import numpy as np
from collections import deque
import fileinput


class LabeledLineSentence:
	"""
		ides:
			Number	
			String
	"""
	def __init__(self, source, ides="Number"):
		self.source = source
		self.sentences = None
		self.ides = ides
		self.doc2vec = None
		#self.fileOpened = utils.smart_open(self.source)
		self.fileOpened = fileinput.input([self.source])
		self.dq = deque(maxlen = 10000)
		self.finishedDoc = False
	

	def __iter__(self):
		return self

	def reloadDoc(self):
		self.finishedDoc = False
		self.fileOpened.close()
		self.fileOpened = fileinput.input([self.source])


	def next(self):
		if len(self.dq) == 0:
			#Load data
			self.loadData()
			if len(self.dq) == 0:
				#
				raise StopIteration()
			else:
				return self.dq.pop()
		else:
			# pop out an element at from the right of the queue
			return self.dq.pop()

	def loadData(self):
		if self.finishedDoc == True:
			return

		while len(self.dq) < self.dq.maxlen:
			last_identif = 0
			try:
				line = self.fileOpened.readline()
			except:
				self.finishedDoc = True
				print "Documento terminado"
				break

			if len(line) < 1:
				self.finishedDoc = True
				print "Documento terminado"
				break
	
			if self.ides == "Number":
				last_identif = long(line)
			else:
				last_identif = line.replace("\n", "")

			line = self.fileOpened.readline()
		
			palabras = line.split()
			palabras_clean = []
			for palabra in palabras:
				if len(palabra) > 1:
					palabras_clean.append(palabra)

			if len(palabras_clean) > 0:
				self.dq.appendleft(TaggedDocument(palabras_clean, [str(last_identif)]))

class Doc2Vec(object):
	"""docstring for Doc2Vec"""
	def __init__(self):
		super(Doc2Vec, self).__init__()
		self.doc2vec = None
		
	def train(self,input_path, save_location, dimension = 50, epochs = 20, method="DBOW", ides="Number"):
		sentences = LabeledLineSentence(input_path, ides)

		total_start = time.time()
		dm_ = 1 
		if method == "DBOW":
			dm_ = 0
		model = gensim.models.Doc2Vec(min_count=1, window=7, size=dimension, dm = dm_, sample=1e-3, negative=5,workers=6, alpha=0.02)
		
		print "inicio vocab"
		model.build_vocab(sentences)
		sentences.reloadDoc()
		print "fin vocab"
		first_alpha = model.alpha
		last_alpha = 0.0001
		#model.min_alpha = 0.0001
		next_alpha = first_alpha
		for epoch in xrange(epochs):
			start = time.time()
			print "iniciando epoca DBOW:"
			print model.alpha
			next_alpha = (((first_alpha - last_alpha) / float(epochs)) * float(epochs - (epoch+1)) + last_alpha)
			model.min_alpha = next_alpha
			model.train(sentences)
			sentences.reloadDoc()
			end = time.time()
			model.alpha = next_alpha
			print "tiempo de la epoca " + str(epoch) +": " + str(end - start)

		model.save(save_location)

		total_end = time.time()

		print "tiempo total:" + str((total_end - total_start)/60.0)


	def simulateVectorsFromVectorText(self, vectorText, modelLocation=None):
		if self.doc2vec is None and modelLocation is None:
			raise Exception("Se tiene que cargar el modelo")

		if self.doc2vec is None:
			self.doc2vec =  gensim.models.Doc2Vec.load(modelLocation)
		
		vector = np.array(self.doc2vec.infer_vector(vectorText, steps=3, alpha=0.1))
		return vector / np.linalg.norm(vector)

	def loadModel(self, modelLocation):
		self.doc2vec =  gensim.models.Doc2Vec.load(modelLocation)

	def getNormalizedTagsVectors(self):
		doctags = self.doc2vec.docvecs.doctags
		ret = {}
		for doctag in doctags:
			vector = np.array(self.doc2vec.docvecs[doctag])
			ret[doctag] = vector / np.linalg.norm(vector)

		return ret