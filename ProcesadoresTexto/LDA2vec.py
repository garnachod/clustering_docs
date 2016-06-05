# -*- coding: utf-8 -*-
from Doc2Vec import LabeledLineSentence
from lda2vec import preprocess, Corpus
#from lda2vec_model import LDA2Vec
from lda2vec import EmbedMixture
from lda2vec import dirichlet_likelihood
from lda2vec.utils import move

from chainer import Chain
import chainer.links as L
import chainer.functions as F

import numpy as np

import pickle
import time
import shelve

import chainer
from chainer import serializers
import chainer.optimizers as O
import numpy as np

from lda2vec import utils
from lda2vec import prepare_topics, print_top_words_per_topic, topic_coherence


"""
	No funciona
"""

class LDA2Vec(object):
	"""docstring for LDA2Vec"""
	def __init__(self):
		super(LDA2Vec, self).__init__()

	def train(self, input_path, save_location, dimension = 50, epochs = 20, ides="Number"):
		max_length = 500
		sentences = LabeledLineSentence(input_path, ides)
		texts = [unicode(" ".join(x.words[:max_length]), errors='ignore') for x in sentences]

		batchsize = 4096


		#print texts[:10]
		tokens, vocab = preprocess.tokenize(texts, max_length, n_threads=4, merge=False)

		# Make a ranked list of rare vs frequent words
		corpus = Corpus()
		corpus.update_word_count(tokens)
		corpus.finalize()
		compact = corpus.to_compact(tokens)

		model = lda2v = LDA2Vec_train(tokens, vocab, n_topics = dimension)

		words = corpus.word_list(vocab)[:lda2v.n_vocab]

		pruned = corpus.filter_count(compact, min_count=2)
		# Convert the compactified arrays into bag of words arrays
		bow = corpus.compact_to_bow(pruned)
		# Words tend to have power law frequency, so selectively
		# downsample the most prevalent words
		clean = corpus.subsample_frequent(pruned)
		# Now flatten a 2D array of document per row and word position
		# per column to a 1D array of words. This will also remove skips
		# and OoV words
		doc_ids = np.arange(pruned.shape[0])
		flattened, (doc_ids,) = corpus.compact_to_flat(pruned, doc_ids)

		# How many tokens are in each document
		doc_idx, lengths = np.unique(doc_ids, return_counts=True)
		doc_lengths = np.zeros(doc_ids.max() + 1, dtype='int32')
		doc_lengths[doc_idx] = lengths

		# Count all token frequencies
		tok_idx, freq = np.unique(flattened, return_counts=True)
		term_frequency = np.zeros(lda2v.n_vocab, dtype='int32')
		term_frequency[tok_idx] = freq

		optimizer = O.Adam()
		optimizer.setup(model)
		clip = chainer.optimizer.GradientClipping(5.0)
		optimizer.add_hook(clip)

		j = 0
		epoch = 0
		fraction = batchsize * 1.0 / flattened.shape[0]
		progress = shelve.open('progress.shelve')
		for epoch in range(40):
			serializers.save_hdf5("lda2vec.hdf5", model)
			data = prepare_topics(model.mixture.weights.W.data.copy(),
						  model.mixture.factors.W.data.copy(),
						  model.sampler.W.data.copy(),
						  words)
			top_words = print_top_words_per_topic(data)
			if j % 100 == 0 and j > 100:
				coherence = topic_coherence(top_words)
				for j in range(dimension):
					print j, coherence[(j, 'cv')]
				kw = dict(top_words=top_words, coherence=coherence, epoch=epoch)
				progress[str(epoch)] = pickle.dumps(kw)
			data['doc_lengths'] = doc_lengths
			data['term_frequency'] = term_frequency
			np.savez('topics.pyldavis', **data)
			for d, f in utils.chunks(batchsize, doc_ids, flattened):
				t0 = time.time()
				optimizer.zero_grads()
				l = model.fit_partial(d.copy(), f.copy())
				prior = model.prior()
				loss = prior * fraction
				loss.backward()
				optimizer.update()
				msg = ("J:{j:05d} E:{epoch:05d} L:{loss:1.3e} "
					   "P:{prior:1.3e} R:{rate:1.3e}")
				t1 = time.time()
				dt = t1 - t0
				rate = batchsize / dt
				logs = dict(loss=float(l), epoch=epoch, j=j,
							prior=float(prior.data), rate=rate)
				print msg.format(**logs)
				j += 1
			

class LDA2Vec_train(Chain):
	def __init__(self, tokens, vocab, n_topics=10, n_units=128, dropout_ratio=0.5, train=True,
				 counts=None, n_samples=5, word_dropout_ratio=0.0, power=0.75):

		self.n_documents = len(tokens)
		self.n_vocab = len(vocab)
		if counts == None:
			term_frequency = np.zeros(self.n_vocab, dtype='int32')
			counts = term_frequency

		em = EmbedMixture(self.n_documents, n_topics, n_units, dropout_ratio=dropout_ratio)
		kwargs = {}
		kwargs['mixture'] = em
		kwargs['sampler'] = L.NegativeSampling(n_units, counts, n_samples, power=power)

		super(LDA2Vec_train, self).__init__(**kwargs)
		rand = np.random.random(self.sampler.W.data.shape)
		self.sampler.W.data[:, :] = rand[:, :]
		self.n_units = n_units
		self.train = train
		self.dropout_ratio = dropout_ratio
		self.word_dropout_ratio = word_dropout_ratio
		self.n_samples = n_samples

	def prior(self):
		dl1 = dirichlet_likelihood(self.mixture.weights)
		return dl1

	def fit_partial(self, rdoc_ids, rword_indices, window=5,
					update_only_docs=False):
		doc_ids, word_indices = move(self.xp, rdoc_ids, rword_indices)
		pivot_idx = next(move(self.xp, rword_indices[window: -window]))
		pivot = F.embed_id(pivot_idx, self.sampler.W)
		if update_only_docs:
			pivot.unchain_backward()
		doc_at_pivot = rdoc_ids[window: -window]
		doc = self.mixture(next(move(self.xp, doc_at_pivot)),
						   update_only_docs=update_only_docs)
		loss = 0.0
		start, end = window, rword_indices.shape[0] - window
		context = (F.dropout(doc, self.dropout_ratio) +
				   F.dropout(pivot, self.dropout_ratio))
		for frame in range(-window, window + 1):
			# Skip predicting the current pivot
			if frame == 0:
				continue
			# Predict word given context and pivot word
			# The target starts before the pivot
			targetidx = rword_indices[start + frame: end + frame]
			doc_at_target = rdoc_ids[start + frame: end + frame]
			doc_is_same = doc_at_target == doc_at_pivot
			rand = np.random.uniform(0, 1, doc_is_same.shape[0])
			mask = (rand > self.word_dropout_ratio).astype('bool')
			weight = np.logical_and(doc_is_same, mask).astype('int32')
			# If weight is 1.0 then targetidx
			# If weight is 0.0 then -1
			targetidx = targetidx * weight + -1 * (1 - weight)
			target, = move(self.xp, targetidx)
			loss = self.sampler(context, target)
			loss.backward()
			if update_only_docs:
				# Wipe out any gradient accumulation on word vectors
				self.sampler.W.grad *= 0.0
		return loss.data


if __name__ == '__main__':
	l2v = LDA2Vec()
	l2v.train("/home/dani/crawler/limpiado.txt", "prueba.txt", ides="Strings")
